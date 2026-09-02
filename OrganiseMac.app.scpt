tell application "Terminal"
    activate
    set scriptPath to POSIX path of ((path to me as text) & "::") & "run_organiser.sh"
    do script quoted form of scriptPath
end tell 