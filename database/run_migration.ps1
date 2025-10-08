# Script PowerShell pour exécuter la migration
# Assurez-vous que PostgreSQL est installé et que psql est dans le PATH

$env:PGPASSWORD = "123456789"  # Votre mot de passe PostgreSQL

# Exécuter la migration
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h localhost -p 5432 -U postgres -d sonaged_reporting -f "migration_add_completion_status.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Migration exécutée avec succès!" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de l'exécution de la migration" -ForegroundColor Red
}
