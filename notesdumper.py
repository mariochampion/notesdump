import subprocess
import os
from datetime import datetime
import argparse

DEFAULT_EXPORT_PATH = "~/Documents/openai/notesdump"
DEFAULT_NOTES_OUTERDIR = "macosnotes"
DEFAULT_GITHUB_URL = "https://github.com/mariochampion/notesdump"



def setup_git_repo(repo_path, DEFAULT_GITHUB_URL):
    """Initialize Git repo and set remote if not already set up"""
    if not os.path.exists(os.path.join(repo_path, '.git')):
        subprocess.run(['git', 'init'], cwd=repo_path)
        subprocess.run(['git', 'remote', 'add', 'origin', DEFAULT_GITHUB_URL], cwd=repo_path)
        subprocess.run(['git', 'branch', '-m', 'main'], cwd=repo_path)
        # Add this to handle remote repository state
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], cwd=repo_path)
        except:
            print("No remote content to pull")

       

def export_notes_to_markdown(export_path, folder_name=None, max_notes=None):
    """Export Notes using osascript with folder and count limits"""
    applescript = f'''
    tell application "Notes"
        if length of "{folder_name if folder_name else ''}" > 0 then
            try
                set targetFolder to folder "{folder_name}"
                set allNotes to every note in targetFolder
                set export_path_full to "{export_path}/{DEFAULT_NOTES_OUTERDIR}/{folder_name}"
            on error
                log "Folder {folder_name} not found"
                return 0
            end try
        else
            set allNotes to every note
        end if
        
        set noteCount to (count of allNotes)
        if {max_notes} > 0 
        	set maxToProcess to {max_notes} 
        else
        	set maxToProcess to noteCount
        end if
        
        if maxToProcess < noteCount
        	set notesToProcess to maxToProcess
        else
        	set notesToProcess to noteCount
        end if
        
        repeat with i from 1 to notesToProcess
            set currentNote to item i of allNotes
            
            set noteTitle to the name of currentNote
            set noteCreationDate to "<div></b>Creation Date:</b> " & creation date of currentNote & "<br></div>"
            set linebreaker to "<div><br></div>"
            set noteContent to the body of currentNote
            
            -- Clean the title for use as filename
            set cleanTitle to do shell script "echo " & quoted form of noteTitle & " | sed 's/[^a-zA-Z0-9.]/-/g' | tr '[:upper:]' '[:lower:]'"
            set fileName to cleanTitle & ".md"
            
            -- Write to file
            do shell script "echo " & quoted form of noteCreationDate & quoted form of linebreaker & quoted form of noteContent & " > " & quoted form of export_path_full & "/" & fileName
        end repeat
        
        return notesToProcess
    end tell
    '''
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    if result.stderr:
        print(f"Error: {result.stderr}")
        return 0
    return int(result.stdout.strip()) if result.stdout.strip() else 0

def commit_and_push(repo_path, folder_name=None):
    """Commit changes and push to GitHub"""
    # Always operate from the git root directory
    result_gitadd = subprocess.run(['git', 'add', f'{DEFAULT_NOTES_OUTERDIR}'], cwd=repo_path)
    if result_gitadd.returncode == 0:
        print(f"Successfully GIT ADDed to origin/main.")
    else:
        print(f"Error GIT ADD to origin/main:")
        print(result_gitadd)
    
    folder_info = f" from folder '{folder_name}'" if folder_name else ""
    commit_message = f"Updated notes{folder_info} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print(f"repo_path:{repo_path}, folder_name:{folder_name}, commit_message:{commit_message}")
    
    result_gitcommit = subprocess.run(['git', 'commit', '-m', commit_message], cwd=repo_path)
    print("past git commit")
    if result_gitcommit.returncode == 0:
        print(f"Successfully COMMITed to origin/main.")
    else:
        print(f"Error COMMITing to origin/main:")
        print(result_gitcommit)
    
    # Try to pull and rebase before pushing
    try:
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], cwd=repo_path)
    except:
        print("No remote changes to pull")
    
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_path, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Successfully pushed to origin/main.")
    else:
        print("Error pushing to origin/main:")
        print(result.stderr)
        # Optionally, try force push if regular push fails
        # result = subprocess.run(['git', 'push', '-f', 'origin', 'main'], cwd=repo_path, capture_output=True, text=True)
   
    

def main():
    parser = argparse.ArgumentParser(description='Export Apple Notes to GitHub')
    parser.add_argument('--folder', type=str, default='',
                      help='Specific Notes folder to export (default: all folders)')
    parser.add_argument('--max-notes', type=int,
                      help='Maximum number of notes to process')
    parser.add_argument('--export-path', type=str, 
                      default=os.path.expanduser(f"{DEFAULT_EXPORT_PATH}"),
                      help=f'Path to export the notes (default: {DEFAULT_EXPORT_PATH})')
    parser.add_argument('--github-url', type=str,
    				  default=DEFAULT_GITHUB_URL,
                      help='GitHub repository URL')
    parser.add_argument('--wrapper-dir', type=str,
    				  default=DEFAULT_NOTES_OUTERDIR,
                      help='Outer directory to hold folders')                      
                      
                      
                      
    
    args = parser.parse_args()
    
    os.makedirs(args.export_path, exist_ok=True)
    if args.folder:
        export_path_w_folder = f"{args.export_path}/{DEFAULT_NOTES_OUTERDIR}/{args.folder}"
        os.makedirs(export_path_w_folder, exist_ok=True)
    
    setup_git_repo(args.export_path, args.github_url)
    
    notes_processed = export_notes_to_markdown(
        args.export_path,
        args.folder,
        args.max_notes
    )
    
    print(f"Processed {notes_processed} notes")
    
    if notes_processed > 0:
        commit_and_push(args.export_path, args.folder)
    else:
        print("No notes were processed, skipping git commit")

if __name__ == "__main__":
    main()