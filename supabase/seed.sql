-- Initialize Projects table
CREATE TABLE projects (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name text NOT NULL,
    description text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (following security best practices from .clinerules)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Add a default policy that allows all operations for authenticated users
CREATE POLICY "Enable all operations for authenticated users" ON projects
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Initialize Versions table (renamed from versions)
CREATE TABLE versions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_number integer NOT NULL DEFAULT 0,
    parent_id uuid REFERENCES versions(id),  -- Renamed from parent_version_id
    name text NOT NULL DEFAULT '',
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(project_id, version_number)
);

-- Add index for faster lookups by project and version number
CREATE INDEX idx_versions_version ON versions(project_id, version_number);

-- Enable Row Level Security
ALTER TABLE versions ENABLE ROW LEVEL SECURITY;

-- Add a default policy that allows all operations for authenticated users
CREATE POLICY "Enable all operations for authenticated users" ON versions
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Initialize Files table
CREATE TABLE files (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    version_id uuid NOT NULL REFERENCES versions(id) ON DELETE CASCADE,  -- Renamed from version_id
    path text NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_version_path UNIQUE (version_id, path),  -- Renamed constraint
    CONSTRAINT ck_file_path_not_empty CHECK (length(path) > 0)
);

-- Add index for faster lookups by version
CREATE INDEX idx_files_version_id ON files(version_id);  -- Renamed index

-- Enable Row Level Security
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Add a default policy that allows all operations for authenticated users
CREATE POLICY "Enable all operations for authenticated users" ON files
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);
