import json
import argparse
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def process_all_repos(organization_url, personal_access_token, project_name, search_text, replace_text, dry_run=True):
    """Search and replace text in JSON files across all repositories"""
    # Setup connection
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    git_client = connection.clients.get_git_client()

    print(f"\nProcessing all repositories in project '{project_name}'...")
    print(f"Search: '{search_text}'")
    print(f"Replace: '{replace_text}'")
    print(f"Dry run: {'ON (no changes will be made)' if dry_run else 'OFF (changes will be committed)'}")
    print("-" * 80)

    # Get all repositories in the project
    repos = git_client.get_repositories(project=project_name)
    total_changes = 0
    total_files = 0

    for repo in repos:
        print(f"\nProcessing repository: {repo.name}")
        repo_changes = 0

        try:
            # Get all JSON files in the repository
            items = git_client.get_items(
                repository_id=repo.id,
                project=project_name,
                scope_path='/',
                recursion_level='full',
                include_content_metadata=True
            )

            for item in items:
                if item.is_folder or not item.path.lower().endswith('.json'):
                    continue

                total_files += 1
                try:
                    # Get file content
                    file_content = git_client.get_item_content(
                        repository_id=repo.id,
                        project=project_name,
                        path=item.path,
                        include_content=True
                    )
                    
                    # Convert to string and parse JSON
                    content = b''.join(file_content).decode('utf-8')
                    json_data = json.loads(content)
                    json_str = json.dumps(json_data)
                    
                    # Search for text
                    if search_text in json_str:
                        print(f"\nFound in: {item.path}")
                        
                        # Replace text
                        new_json_str = json_str.replace(search_text, replace_text)
                        changes = json_str.count(search_text)
                        
                        print(f"Changes needed: {changes}")
                        print("Old value:", search_text)
                        print("New value:", replace_text)
                        
                        if not dry_run:
                            # Save changes
                            new_data = json.loads(new_json_str)
                            new_content = json.dumps(new_data, indent=2)
                            
                            # Get latest commit
                            refs = git_client.get_refs(
                                project=project_name,
                                repository_id=repo.id,
                                filter=f"heads/{repo.default_branch}"
                            )
                            if not refs:
                                print(f"Error: Default branch not found for {repo.name}")
                                continue
                                
                            latest_commit = refs[0]
                            
                            # Prepare the change
                            change = {
                                'changeType': 'edit',
                                'item': {'path': item.path},
                                'newContent': {
                                    'content': new_content,
                                    'contentType': 'rawtext'
                                }
                            }
                            
                            # Create push with the change
                            push = {
                                'refUpdates': [{
                                    'name': f'refs/heads/{repo.default_branch}',
                                    'oldObjectId': latest_commit.object_id
                                }],
                                'commits': [{
                                    'comment': f"Replaced '{search_text}' with '{replace_text}'",
                                    'changes': [change]
                                }]
                            }
                            
                            git_client.create_push(
                                push=push,
                                project=project_name,
                                repository_id=repo.id
                            )
                            print("Changes committed successfully")
                        
                        repo_changes += changes
                        total_changes += changes

                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON file: {item.path}")
                except Exception as e:
                    print(f"Error processing {item.path}: {str(e)}")

            print(f"\nSummary for {repo.name}:")
            print(f"Files processed: {sum(1 for i in items if not i.is_folder and i.path.lower().endswith('.json'))}")
            print(f"Changes made: {repo_changes}")

        except Exception as e:
            print(f"Error accessing repository {repo.name}: {str(e)}")

    print("\n=== FINAL SUMMARY ===")
    print(f"Total repositories processed: {len(repos)}")
    print(f"Total JSON files scanned: {total_files}")
    print(f"Total replacements made: {total_changes}")
    
    if dry_run and total_changes > 0:
        print("\nNOTE: This was a dry run. No changes were actually made.")
        print("To make the changes, run with --no-dry-run")

def main():
    parser = argparse.ArgumentParser(description='Search and replace in JSON files across all repositories')
    parser.add_argument('--org', required=True, help='Azure DevOps organization URL')
    parser.add_argument('--pat', required=True, help='Personal Access Token')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--search', required=True, help='Text to search for')
    parser.add_argument('--replace', required=True, help='Text to replace with')
    parser.add_argument('--no-dry-run', dest='dry_run', action='store_false', 
                       help='Actually make changes (default is dry-run)')
    args = parser.parse_args()

    process_all_repos(
        organization_url=args.org,
        personal_access_token=args.pat,
        project_name=args.project,
        search_text=args.search,
        replace_text=args.replace,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()