DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'memory_projects_project_id_not_all'
  ) THEN
    ALTER TABLE memory_projects
      ADD CONSTRAINT memory_projects_project_id_not_all
      CHECK (project_id <> 'all') NOT VALID;
  END IF;
END $$;
