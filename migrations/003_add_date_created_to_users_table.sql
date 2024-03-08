-- add confirmation email to token
-- performing the check to ensure there will be no errors when the scripts are ran multipel times and it won't block the next script.
DO $$
BEGIN
    -- add the date the user was created
    IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'date_created') THEN
        EXECUTE 'ALTER TABLE users ADD COLUMN date_created TIMESTAMP DEFAULT NOW()';
    END IF;

    -- add date a modification was done
    IF NOT EXISTS (SELECT * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'date_modified') THEN
        EXECUTE 'ALTER TABLE users ADD COLUMN date_modified TIMESTAMP';
    END IF;
END $$;