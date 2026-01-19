-- SQL Script to Reset Database User IDs

-- Option 1: TRUNCATE (fastest, reset all data and auto-increment)
-- Use this if you want to delete ALL users and reset ID to 1
TRUNCATE TABLE messages;
TRUNCATE TABLE chats;
TRUNCATE TABLE user_files;
TRUNCATE TABLE otp_tokens;
-- If you have foreign key constraints, you may need to disable them first:
-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE users;
-- SET FOREIGN_KEY_CHECKS = 1;
TRUNCATE TABLE users;

-- Option 2: DELETE + ALTER (if TRUNCATE doesn't work due to foreign keys)
-- DELETE FROM messages;
-- DELETE FROM chats;
-- DELETE FROM user_files;
-- DELETE FROM otp_tokens;
-- DELETE FROM users;
-- ALTER TABLE users AUTO_INCREMENT = 1;

-- After running this, the next user created will have ID = 1
