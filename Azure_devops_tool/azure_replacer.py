import json
import re
import argparse
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Simple JSON Search/Replace in Azure DevOps')
    parser.add_argument('--org', required=True, help='Your Azure DevOps organization URL')
    parser.add_argument('--pat', required=True, help='Your Personal Access Token')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--branch', default='main', help='Branch name (default: main)')
    parser.add_argument('--search', required=True, help='Text to search for')
    parser.add_argument('--replace', help='Text to replace with (omit for search only)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    args = parser.parse_args()

    # Connect to Azure DevOps
    credentials = BasicAuthentication('', args.pat)
    connection = Connection(base_url=args.org, creds=credentials)
    git_client = connection.clients.get_git_client()

    # Get all JSON files in the repository
    print(f"\nSearching JSON files in {args.project}/{args.repo}...")
    
    # Prepare to track results
    files_changed = 0
    replacements_made = 0
    
    # Get the list of files
    items = git_client.get_items(
        repository_id=args.repo,
        project=args.project,
        scope_path='/',
        recursion_level='full',
        include_content_metadata=True
    )

    # Process each file
    for item in items:
        # Skip folders and non-JSON files
        if item.is_folder or not item.path.lower().endswith('.json'):
            continue

        print(f"\nChecking file: {item.path}")

        try:
            # Get file content
            file_content = git_client.get_item_text(
                repository_id=args.repo,
                project=args.project,
                path=item.path,
                include_content=True
            )
            content = b''.join(file_content).decode('utf-8')          
            # Parse JSON
            data = json.loads(content)
            
            # Convert back to string to search (simple approach)
            json_str = json.dumps(data)
            
            # Search for text
            if args.search in json_str:
                print(f"Found '{args.search}' in {item.path}")
                
                if args.replace:
                    # Replace text
                    new_json_str = json_str.replace(args.search, args.replace)
                    replace_count = json_str.count(args.search)
                    
                    # Count how many replacements were made
                    replacements_made += replace_count
                    
                    print(f"Would make {replace_count} replacements")
                    print("Old value:", args.search)
                    print("New value:", args.replace)
                    
                    if not args.dry_run:
                        # Save changes
                        print("Saving changes...")
                        new_data = json.loads(new_json_str)
                        new_content = json.dumps(new_data, indent=2)
                        
                        # Get latest commit
                        refs = git_client.get_refs(
                            project=args.project,
                            repository_id=args.repo,
                            filter=f"heads/{args.branch}"
                        )
                        if not refs:
                            print(f"Error: Branch {args.branch} not found")
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
                                'name': f'refs/heads/{args.branch}',
                                'oldObjectId': latest_commit.object_id
                            }],
                            'commits': [{
                                'comment': f"Replaced '{args.search}' with '{args.replace}'",
                                'changes': [change]
                            }]
                        }
                        
                        git_client.create_push(
                            push=push,
                            project=args.project,
                            repository_id=args.repo
                        )
                        files_changed += 1
            else:
                print("No matches found in this file")
                
        except json.JSONDecodeError:
            print("Skipping - Not valid JSON")
        except Exception as e:
            print(f"Error: {str(e)}")

    print("\n=== Summary ===")
    print(f"Total replacements: {replacements_made}")
    print(f"Files changed: {files_changed}")
    
    if args.dry_run and args.replace:
        print("\nNOTE: Run without --dry-run to actually save changes")

if __name__ == "__main__":
    main()