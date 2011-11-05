until python app.py; do
    echo "Server crashed bye bye with exit code $?. Respawning.." >&2
    sleep 1
done
