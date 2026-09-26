-- ============================================================
-- AI 驱动的个人知识库与智能学习平台
-- Database: fastapi_demo
-------------------------

-- 说明：
-- 1. 本文件仅用于初始化项目数据库表结构
-- 2. 不包含任何真实业务数据
-- 3. 不包含数据库账号、密码、API Key 等敏感信息
-- 4. 请先创建 fastapi_demo 数据库，再执行本文件
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 用户表
-- ============================================================

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
`id` INT NOT NULL AUTO_INCREMENT,
`username` VARCHAR(50) DEFAULT NULL,
`age` INT DEFAULT NULL,
`password` VARCHAR(255) DEFAULT NULL,
`email` VARCHAR(255) DEFAULT NULL,
`phone` VARCHAR(20) DEFAULT NULL,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (`id`),
UNIQUE KEY `uk_users_username` (`username`),
UNIQUE KEY `uk_users_email` (`email`),
UNIQUE KEY `uk_users_phone` (`phone`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 文件表
-- ============================================================

DROP TABLE IF EXISTS `files`;

CREATE TABLE `files` (
`id` INT NOT NULL AUTO_INCREMENT,
`filename` VARCHAR(255) DEFAULT NULL,
`file_path` VARCHAR(255) DEFAULT NULL,
`user_id` INT DEFAULT NULL,
`created_time` DATETIME DEFAULT NULL,
`file_size` INT DEFAULT NULL,
PRIMARY KEY (`id`),
INDEX `idx_files_user_id` (`user_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 文档表
-- ============================================================

DROP TABLE IF EXISTS `documents`;

CREATE TABLE `documents` (
`id` INT NOT NULL AUTO_INCREMENT,
`user_id` INT NOT NULL,
`file_id` INT DEFAULT NULL,
`content` TEXT DEFAULT NULL,
`created_time` DATETIME DEFAULT NULL,
`status` VARCHAR(20) NOT NULL DEFAULT 'processing',
`chunk_count` INT NOT NULL DEFAULT 0,
PRIMARY KEY (`id`),
INDEX `idx_documents_user_id` (`user_id`),
INDEX `idx_documents_file_id` (`file_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 文档切片表
-- ============================================================

DROP TABLE IF EXISTS `chunks`;

CREATE TABLE `chunks` (
`id` INT NOT NULL AUTO_INCREMENT,
`document_id` INT DEFAULT NULL,
`content` TEXT DEFAULT NULL,
`chunk_index` INT NOT NULL DEFAULT 0,
PRIMARY KEY (`id`),
INDEX `idx_chunks_document_id` (`document_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 对话表
-- ============================================================

DROP TABLE IF EXISTS `conversations`;

CREATE TABLE `conversations` (
`id` INT NOT NULL AUTO_INCREMENT,
`user_id` INT NOT NULL,
`title` VARCHAR(255) DEFAULT '新对话',
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP,
PRIMARY KEY (`id`),
INDEX `idx_conversations_user_id` (`user_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 对话消息表
-- ============================================================

DROP TABLE IF EXISTS `messages`;

CREATE TABLE `messages` (
`id` INT NOT NULL AUTO_INCREMENT,
`conversation_id` INT NOT NULL,
`role` VARCHAR(20) NOT NULL,
`content` TEXT NOT NULL,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (`id`),
INDEX `idx_messages_conversation_id` (`conversation_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 简历表
-- ============================================================

DROP TABLE IF EXISTS `resumes`;

CREATE TABLE `resumes` (
`id` INT NOT NULL AUTO_INCREMENT,
`user_id` INT NOT NULL,
`filename` VARCHAR(255) NOT NULL,
`file_path` VARCHAR(500) NOT NULL,
`content` TEXT DEFAULT NULL,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP,
`structured_data` JSON DEFAULT NULL,
PRIMARY KEY (`id`),
INDEX `idx_resumes_user_id` (`user_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 模拟面试表
-- ============================================================

DROP TABLE IF EXISTS `interviews`;

CREATE TABLE `interviews` (
`id` INT NOT NULL AUTO_INCREMENT,
`user_id` INT NOT NULL,
`resume_id` INT NOT NULL,
`status` VARCHAR(20) DEFAULT 'ongoing',
`current_question` TEXT DEFAULT NULL,
`total_score` INT DEFAULT 0,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP,
`report` JSON DEFAULT NULL,
`title` VARCHAR(255) DEFAULT NULL,
PRIMARY KEY (`id`),
INDEX `idx_interviews_user_id` (`user_id`),
INDEX `idx_interviews_resume_id` (`resume_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 模拟面试消息表
-- ============================================================

DROP TABLE IF EXISTS `interview_messages`;

CREATE TABLE `interview_messages` (
`id` INT NOT NULL AUTO_INCREMENT,
`interview_id` INT NOT NULL,
`role` VARCHAR(20) NOT NULL,
`content` TEXT NOT NULL,
`score` INT DEFAULT NULL,
`feedback` TEXT DEFAULT NULL,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
`reference_answer` TEXT DEFAULT NULL,
`knowledge_gap` JSON DEFAULT NULL,
PRIMARY KEY (`id`),
INDEX `idx_interview_messages_interview_id` (`interview_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 验证码表
-- ============================================================

DROP TABLE IF EXISTS `verification_codes`;

CREATE TABLE `verification_codes` (
`id` INT NOT NULL AUTO_INCREMENT,
`target` VARCHAR(255) NOT NULL,
`code` VARCHAR(10) NOT NULL,
`type` VARCHAR(20) NOT NULL,
`expires_at` DATETIME NOT NULL,
`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (`id`),
INDEX `idx_verification_target` (`target`),
INDEX `idx_verification_type` (`type`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
