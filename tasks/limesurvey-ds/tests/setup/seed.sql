/*M!999999\- enable the sandbox mode */ 

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;
DROP TABLE IF EXISTS `lime_answer_l10ns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_answer_l10ns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `aid` int(11) NOT NULL,
  `answer` mediumtext NOT NULL,
  `language` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_answer_l10ns_idx` (`aid`,`language`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_answer_l10ns` WRITE;
/*!40000 ALTER TABLE `lime_answer_l10ns` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_answer_l10ns` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_answers` (
  `aid` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL,
  `code` varchar(5) NOT NULL,
  `sortorder` int(11) NOT NULL,
  `assessment_value` int(11) NOT NULL DEFAULT 0,
  `scale_id` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`aid`),
  KEY `lime_answers_idx` (`qid`,`code`,`scale_id`),
  KEY `lime_answers_idx2` (`sortorder`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_answers` WRITE;
/*!40000 ALTER TABLE `lime_answers` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_answers` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_archived_table_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_archived_table_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `survey_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `tbl_name` varchar(255) NOT NULL,
  `tbl_type` varchar(10) NOT NULL,
  `created` datetime NOT NULL,
  `properties` text NOT NULL,
  `attributes` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_archived_table_settings` WRITE;
/*!40000 ALTER TABLE `lime_archived_table_settings` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_archived_table_settings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_assessments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) NOT NULL DEFAULT 0,
  `scope` varchar(5) NOT NULL,
  `gid` int(11) NOT NULL DEFAULT 0,
  `name` text NOT NULL,
  `minimum` varchar(50) NOT NULL,
  `maximum` varchar(50) NOT NULL,
  `message` mediumtext NOT NULL,
  `language` varchar(20) NOT NULL DEFAULT 'en',
  PRIMARY KEY (`id`,`language`),
  KEY `lime_assessments_idx2` (`sid`),
  KEY `lime_assessments_idx3` (`gid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_assessments` WRITE;
/*!40000 ALTER TABLE `lime_assessments` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_assessments` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_asset_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_asset_version` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` text NOT NULL,
  `version` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_asset_version` WRITE;
/*!40000 ALTER TABLE `lime_asset_version` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_asset_version` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_boxes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_boxes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position` int(11) DEFAULT NULL,
  `url` text NOT NULL,
  `title` text NOT NULL,
  `buttontext` varchar(255) DEFAULT NULL,
  `ico` varchar(255) DEFAULT NULL,
  `desc` text NOT NULL,
  `page` text NOT NULL,
  `usergroup` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_boxes` WRITE;
/*!40000 ALTER TABLE `lime_boxes` DISABLE KEYS */;
INSERT INTO `lime_boxes` VALUES
(1,1,'dashboard/view','Dashboard','View dashboard','ri-function-fill','View dashboard','welcome',-1),
(2,2,'admin/globalsettings','Global settings','View global settings','ri-settings-3-fill','Edit global settings','welcome',-2),
(3,3,'themeOptions','Themes','Edit themes','ri-paint-fill','The themes functionality allows you to edit survey-, admin- or question themes.','welcome',-2),
(4,4,'userManagement/index','Manage administrators','Manage administrators','ri-group-line','The user management allows you to add additional users to your survey administration.','welcome',-2),
(5,5,'admin/pluginmanager/sa/index','Plugins','Manage plugins','ri-plug-fill','Plugins can be used to add custom features','welcome',-2);
/*!40000 ALTER TABLE `lime_boxes` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_conditions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_conditions` (
  `cid` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL DEFAULT 0,
  `cqid` int(11) NOT NULL DEFAULT 0,
  `cfieldname` varchar(50) NOT NULL DEFAULT '',
  `method` varchar(5) NOT NULL DEFAULT '',
  `value` varchar(255) NOT NULL DEFAULT '',
  `scenario` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`cid`),
  KEY `lime_conditions_idx` (`qid`),
  KEY `lime_conditions_idx3` (`cqid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_conditions` WRITE;
/*!40000 ALTER TABLE `lime_conditions` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_conditions` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_defaultvalue_l10ns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_defaultvalue_l10ns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dvid` int(11) NOT NULL DEFAULT 0,
  `language` varchar(20) NOT NULL,
  `defaultvalue` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_defaultvalue_ls` (`dvid`,`language`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_defaultvalue_l10ns` WRITE;
/*!40000 ALTER TABLE `lime_defaultvalue_l10ns` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_defaultvalue_l10ns` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_defaultvalues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_defaultvalues` (
  `dvid` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL DEFAULT 0,
  `scale_id` int(11) NOT NULL DEFAULT 0,
  `sqid` int(11) NOT NULL DEFAULT 0,
  `specialtype` varchar(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`dvid`),
  KEY `lime_idx1_defaultvalue` (`qid`,`scale_id`,`sqid`,`specialtype`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_defaultvalues` WRITE;
/*!40000 ALTER TABLE `lime_defaultvalues` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_defaultvalues` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_expression_errors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_expression_errors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `errortime` varchar(50) DEFAULT NULL,
  `sid` int(11) DEFAULT NULL,
  `gid` int(11) DEFAULT NULL,
  `qid` int(11) DEFAULT NULL,
  `gseq` int(11) DEFAULT NULL,
  `qseq` int(11) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `eqn` text DEFAULT NULL,
  `prettyprint` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_expression_errors` WRITE;
/*!40000 ALTER TABLE `lime_expression_errors` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_expression_errors` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_failed_emails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_failed_emails` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `surveyid` int(11) NOT NULL,
  `responseid` int(11) NOT NULL,
  `email_type` varchar(200) NOT NULL,
  `recipient` varchar(320) NOT NULL,
  `language` varchar(20) NOT NULL DEFAULT 'en',
  `error_message` text DEFAULT NULL,
  `created` datetime NOT NULL,
  `status` varchar(20) DEFAULT 'SEND FAILED',
  `updated` datetime DEFAULT NULL,
  `resend_vars` mediumtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_failed_emails` WRITE;
/*!40000 ALTER TABLE `lime_failed_emails` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_failed_emails` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_failed_login_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_failed_login_attempts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(40) NOT NULL,
  `last_attempt` varchar(20) NOT NULL,
  `number_attempts` int(11) NOT NULL,
  `is_frontend` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_failed_login_attempts` WRITE;
/*!40000 ALTER TABLE `lime_failed_login_attempts` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_failed_login_attempts` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_group_l10ns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_group_l10ns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `gid` int(11) NOT NULL,
  `group_name` text NOT NULL,
  `description` mediumtext DEFAULT NULL,
  `language` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_idx1_group_ls` (`gid`,`language`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_group_l10ns` WRITE;
/*!40000 ALTER TABLE `lime_group_l10ns` DISABLE KEYS */;
INSERT INTO `lime_group_l10ns` VALUES
(1,1,'g1','','en');
/*!40000 ALTER TABLE `lime_group_l10ns` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_groups` (
  `gid` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) NOT NULL DEFAULT 0,
  `group_order` int(11) NOT NULL DEFAULT 0,
  `randomization_group` varchar(20) NOT NULL DEFAULT '',
  `grelevance` text DEFAULT NULL,
  PRIMARY KEY (`gid`),
  KEY `lime_idx1_groups` (`sid`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_groups` WRITE;
/*!40000 ALTER TABLE `lime_groups` DISABLE KEYS */;
INSERT INTO `lime_groups` VALUES
(1,186734,0,'','');
/*!40000 ALTER TABLE `lime_groups` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_label_l10ns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_label_l10ns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `label_id` int(11) NOT NULL,
  `title` text DEFAULT NULL,
  `language` varchar(20) NOT NULL DEFAULT 'en',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_label_l10ns` WRITE;
/*!40000 ALTER TABLE `lime_label_l10ns` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_label_l10ns` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_labels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_labels` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lid` int(11) NOT NULL DEFAULT 0,
  `code` varchar(20) NOT NULL DEFAULT '',
  `sortorder` int(11) NOT NULL,
  `assessment_value` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_idx5_labels` (`lid`,`code`),
  KEY `lime_idx1_labels` (`code`),
  KEY `lime_idx2_labels` (`sortorder`),
  KEY `lime_idx4_labels` (`lid`,`sortorder`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_labels` WRITE;
/*!40000 ALTER TABLE `lime_labels` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_labels` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_labelsets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_labelsets` (
  `lid` int(11) NOT NULL AUTO_INCREMENT,
  `owner_id` int(11) DEFAULT NULL,
  `label_name` varchar(100) NOT NULL DEFAULT '',
  `languages` varchar(255) NOT NULL,
  PRIMARY KEY (`lid`),
  KEY `lime_idx1_labelsets` (`owner_id`),
  KEY `lime_idx2_labelsets` (`lid`,`owner_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_labelsets` WRITE;
/*!40000 ALTER TABLE `lime_labelsets` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_labelsets` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_map_tutorial_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_map_tutorial_users` (
  `tid` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `taken` int(11) DEFAULT 1,
  PRIMARY KEY (`uid`,`tid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_map_tutorial_users` WRITE;
/*!40000 ALTER TABLE `lime_map_tutorial_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_map_tutorial_users` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_message` (
  `id` int(11) NOT NULL,
  `language` varchar(50) NOT NULL DEFAULT '',
  `translation` text DEFAULT NULL,
  PRIMARY KEY (`id`,`language`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_message` WRITE;
/*!40000 ALTER TABLE `lime_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_message` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `entity` varchar(15) NOT NULL,
  `entity_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` mediumtext NOT NULL,
  `status` varchar(15) NOT NULL DEFAULT 'new',
  `importance` int(11) NOT NULL DEFAULT 1,
  `display_class` varchar(31) DEFAULT 'default',
  `hash` varchar(64) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `first_read` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_notifications_pk` (`entity`,`entity_id`,`status`),
  KEY `lime_idx1_notifications` (`hash`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_notifications` WRITE;
/*!40000 ALTER TABLE `lime_notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_notifications` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participant_attribute`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participant_attribute` (
  `participant_id` varchar(50) NOT NULL,
  `attribute_id` int(11) NOT NULL,
  `value` text NOT NULL,
  PRIMARY KEY (`participant_id`,`attribute_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participant_attribute` WRITE;
/*!40000 ALTER TABLE `lime_participant_attribute` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_participant_attribute` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participant_attribute_names`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participant_attribute_names` (
  `attribute_id` int(11) NOT NULL AUTO_INCREMENT,
  `attribute_type` varchar(4) NOT NULL,
  `defaultname` varchar(255) NOT NULL,
  `visible` varchar(5) NOT NULL,
  `encrypted` varchar(5) NOT NULL,
  `core_attribute` varchar(5) NOT NULL,
  PRIMARY KEY (`attribute_id`,`attribute_type`),
  KEY `lime_idx_participant_attribute_names` (`attribute_id`,`attribute_type`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participant_attribute_names` WRITE;
/*!40000 ALTER TABLE `lime_participant_attribute_names` DISABLE KEYS */;
INSERT INTO `lime_participant_attribute_names` VALUES
(1,'TB','firstname','TRUE','Y','Y'),
(2,'TB','lastname','TRUE','Y','Y'),
(3,'TB','email','TRUE','Y','Y');
/*!40000 ALTER TABLE `lime_participant_attribute_names` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participant_attribute_names_lang`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participant_attribute_names_lang` (
  `attribute_id` int(11) NOT NULL,
  `attribute_name` varchar(255) NOT NULL,
  `lang` varchar(20) NOT NULL,
  PRIMARY KEY (`attribute_id`,`lang`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participant_attribute_names_lang` WRITE;
/*!40000 ALTER TABLE `lime_participant_attribute_names_lang` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_participant_attribute_names_lang` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participant_attribute_values`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participant_attribute_values` (
  `value_id` int(11) NOT NULL AUTO_INCREMENT,
  `attribute_id` int(11) NOT NULL,
  `value` mediumtext NOT NULL,
  PRIMARY KEY (`value_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participant_attribute_values` WRITE;
/*!40000 ALTER TABLE `lime_participant_attribute_values` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_participant_attribute_values` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participant_shares`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participant_shares` (
  `participant_id` varchar(50) NOT NULL,
  `share_uid` int(11) NOT NULL,
  `date_added` datetime NOT NULL,
  `can_edit` varchar(5) NOT NULL,
  PRIMARY KEY (`participant_id`,`share_uid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participant_shares` WRITE;
/*!40000 ALTER TABLE `lime_participant_shares` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_participant_shares` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_participants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_participants` (
  `participant_id` varchar(50) NOT NULL,
  `firstname` text DEFAULT NULL,
  `lastname` text DEFAULT NULL,
  `email` text DEFAULT NULL,
  `language` varchar(40) DEFAULT NULL,
  `blacklisted` varchar(1) NOT NULL,
  `owner_uid` int(11) NOT NULL,
  `created_by` int(11) NOT NULL,
  `created` datetime DEFAULT NULL,
  `modified` datetime DEFAULT NULL,
  PRIMARY KEY (`participant_id`),
  KEY `lime_idx3_participants` (`language`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_participants` WRITE;
/*!40000 ALTER TABLE `lime_participants` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_participants` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `entity` varchar(50) NOT NULL,
  `entity_id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `permission` varchar(100) NOT NULL,
  `create_p` int(11) NOT NULL DEFAULT 0,
  `read_p` int(11) NOT NULL DEFAULT 0,
  `update_p` int(11) NOT NULL DEFAULT 0,
  `delete_p` int(11) NOT NULL DEFAULT 0,
  `import_p` int(11) NOT NULL DEFAULT 0,
  `export_p` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_idx1_permissions` (`entity_id`,`entity`,`permission`,`uid`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_permissions` WRITE;
/*!40000 ALTER TABLE `lime_permissions` DISABLE KEYS */;
INSERT INTO `lime_permissions` VALUES
(1,'global',0,1,'superadmin',0,1,0,0,0,0),
(2,'global',0,2,'auth_db',0,1,0,0,0,0);
/*!40000 ALTER TABLE `lime_permissions` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_permissiontemplates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_permissiontemplates` (
  `ptid` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(127) NOT NULL,
  `description` text DEFAULT NULL,
  `renewed_last` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `created_by` int(11) NOT NULL,
  PRIMARY KEY (`ptid`),
  UNIQUE KEY `lime_idx1_name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_permissiontemplates` WRITE;
/*!40000 ALTER TABLE `lime_permissiontemplates` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_permissiontemplates` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_plugin_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_plugin_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plugin_id` int(11) NOT NULL,
  `model` varchar(50) DEFAULT NULL,
  `model_id` int(11) DEFAULT NULL,
  `key` varchar(50) NOT NULL,
  `value` mediumtext DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_plugin_settings` WRITE;
/*!40000 ALTER TABLE `lime_plugin_settings` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_plugin_settings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_plugins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_plugins` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `plugin_type` varchar(6) DEFAULT 'user',
  `active` int(11) NOT NULL DEFAULT 0,
  `priority` int(11) NOT NULL DEFAULT 0,
  `version` varchar(32) DEFAULT NULL,
  `load_error` int(11) DEFAULT 0,
  `load_error_message` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_plugins` WRITE;
/*!40000 ALTER TABLE `lime_plugins` DISABLE KEYS */;
INSERT INTO `lime_plugins` VALUES
(1,'UpdateCheck','core',1,0,'1.0.0',0,NULL),
(2,'PasswordRequirement','core',1,0,'1.0.0',0,NULL),
(3,'ComfortUpdateChecker','core',1,0,'1.0.0',0,NULL),
(4,'Authdb','core',1,0,'1.0.0',0,NULL),
(5,'AuthLDAP','core',0,0,'1.0.0',0,NULL),
(6,'AuditLog','core',0,0,'1.0.0',0,NULL),
(7,'Authwebserver','core',0,0,'1.0.0',0,NULL),
(8,'ExportR','core',1,0,'1.0.0',0,NULL),
(9,'ExportSTATAxml','core',1,0,'1.0.0',0,NULL),
(10,'ExportSPSSsav','core',1,0,'1.0.0',0,NULL),
(11,'oldUrlCompat','core',0,0,'1.0.0',0,NULL),
(12,'expressionQuestionHelp','core',0,0,'1.0.0',0,NULL),
(13,'expressionQuestionForAll','core',0,0,'1.0.0',0,NULL),
(14,'expressionFixedDbVar','core',0,0,'1.0.0',0,NULL),
(15,'customToken','core',0,0,'1.0.1',0,NULL),
(16,'mailSenderToFrom','core',0,0,'1.0.0',0,NULL),
(17,'TwoFactorAdminLogin','core',0,0,'1.2.5',0,NULL);
/*!40000 ALTER TABLE `lime_plugins` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_question_attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_question_attributes` (
  `qaid` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL DEFAULT 0,
  `attribute` varchar(50) DEFAULT NULL,
  `value` mediumtext DEFAULT NULL,
  `language` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`qaid`),
  KEY `lime_idx1_question_attributes` (`qid`),
  KEY `lime_idx2_question_attributes` (`attribute`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_question_attributes` WRITE;
/*!40000 ALTER TABLE `lime_question_attributes` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_question_attributes` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_question_l10ns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_question_l10ns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `qid` int(11) NOT NULL,
  `question` mediumtext NOT NULL,
  `help` mediumtext DEFAULT NULL,
  `script` text DEFAULT NULL,
  `language` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_idx1_question_ls` (`qid`,`language`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_question_l10ns` WRITE;
/*!40000 ALTER TABLE `lime_question_l10ns` DISABLE KEYS */;
INSERT INTO `lime_question_l10ns` VALUES
(1,1,'','',NULL,'en'),
(2,2,'','',NULL,'en');
/*!40000 ALTER TABLE `lime_question_l10ns` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_question_themes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_question_themes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `visible` varchar(1) DEFAULT NULL,
  `xml_path` varchar(255) DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `title` varchar(100) NOT NULL,
  `creation_date` datetime DEFAULT NULL,
  `author` varchar(150) DEFAULT NULL,
  `author_email` varchar(255) DEFAULT NULL,
  `author_url` varchar(255) DEFAULT NULL,
  `copyright` text DEFAULT NULL,
  `license` text DEFAULT NULL,
  `version` varchar(45) DEFAULT NULL,
  `api_version` varchar(45) NOT NULL,
  `description` text DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `theme_type` varchar(150) DEFAULT NULL,
  `question_type` varchar(150) NOT NULL,
  `core_theme` tinyint(1) DEFAULT NULL,
  `extends` varchar(150) DEFAULT NULL,
  `group` varchar(150) DEFAULT NULL,
  `settings` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_question_themes` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_question_themes` WRITE;
/*!40000 ALTER TABLE `lime_question_themes` DISABLE KEYS */;
INSERT INTO `lime_question_themes` VALUES
(1,'5pointchoice','Y','application/views/survey/questions/answer/5pointchoice','/assets/images/screenshots/5.png','5 point choice','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','5 point choice question type configuration','2019-09-23 15:05:59',1,'question_theme','5',1,'','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"choice-5-pt-radio\"}'),
(2,'arrays/10point','Y','application/views/survey/questions/answer/arrays/10point','/assets/images/screenshots/B.png','Array (10 point choice)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (10 point choice) question type configuration','2019-09-23 15:05:59',1,'question_theme','B',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-10-pt\"}'),
(3,'arrays/5point','Y','application/views/survey/questions/answer/arrays/5point','/assets/images/screenshots/A.png','Array (5 point choice)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (5 point choice) question type configuration','2019-09-23 15:05:59',1,'question_theme','A',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-5-pt\"}'),
(4,'arrays/array','Y','application/views/survey/questions/answer/arrays/array','/assets/images/screenshots/F.png','Array','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array question type configuration','2019-09-23 15:05:59',1,'question_theme','F',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-flexible-row\"}'),
(5,'arrays/column','Y','application/views/survey/questions/answer/arrays/column','/assets/images/screenshots/H.png','Array by column','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array by column question type configuration','2019-09-23 15:05:59',1,'question_theme','H',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-flexible-column\"}'),
(6,'arrays/dualscale','Y','application/views/survey/questions/answer/arrays/dualscale','/assets/images/screenshots/1.png','Array dual scale','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array dual scale question type configuration','2019-09-23 15:05:59',1,'question_theme','1',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"2\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-flexible-dual-scale\"}'),
(7,'arrays/increasesamedecrease','Y','application/views/survey/questions/answer/arrays/increasesamedecrease','/assets/images/screenshots/E.png','Array (Increase/Same/Decrease)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (Increase/Same/Decrease) question type configuration','2019-09-23 15:05:59',1,'question_theme','E',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-increase-same-decrease\"}'),
(8,'arrays/multiflexi','Y','application/views/survey/questions/answer/arrays/multiflexi','/assets/images/screenshots/COLON.png','Array (Numbers)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (Numbers) question type configuration','2019-09-23 15:05:59',1,'question_theme',':',1,'','Arrays','{\"subquestions\":\"2\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-multi-flexi\"}'),
(9,'arrays/texts','Y','application/views/survey/questions/answer/arrays/texts','/assets/images/screenshots/;.png','Array (Texts)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (Texts) question type configuration','2019-09-23 15:05:59',1,'question_theme',';',1,'','Arrays','{\"subquestions\":\"2\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"array-multi-flexi-text\"}'),
(10,'arrays/yesnouncertain','Y','application/views/survey/questions/answer/arrays/yesnouncertain','/assets/images/screenshots/C.png','Array (Yes/No/Uncertain)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Array (Yes/No/Uncertain) question type configuration','2019-09-23 15:05:59',1,'question_theme','C',1,'','Arrays','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"array-yes-uncertain-no\"}'),
(11,'boilerplate','Y','application/views/survey/questions/answer/boilerplate','/assets/images/screenshots/X.png','Text display','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Text display question type configuration','2019-09-23 15:05:59',1,'question_theme','X',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"boilerplate\"}'),
(12,'date','Y','application/views/survey/questions/answer/date','/assets/images/screenshots/D.png','Date/Time','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Date/Time question type configuration','2019-09-23 15:05:59',1,'question_theme','D',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"date\"}'),
(13,'equation','Y','application/views/survey/questions/answer/equation','/assets/images/screenshots/EQUATION.png','Equation','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Equation question type configuration','2019-09-23 15:05:59',1,'question_theme','*',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"equation\"}'),
(14,'file_upload','Y','application/views/survey/questions/answer/file_upload','/assets/images/screenshots/PIPE.png','File upload','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','File upload question type configuration','2019-09-23 15:05:59',1,'question_theme','|',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"upload-files\"}'),
(15,'gender','Y','application/views/survey/questions/answer/gender','/assets/images/screenshots/G.png','Gender','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Gender question type configuration','2019-09-23 15:05:59',1,'question_theme','G',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"gender\"}'),
(16,'hugefreetext','Y','application/views/survey/questions/answer/hugefreetext','/assets/images/screenshots/U.png','Huge free text','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Huge free text question type configuration','2019-09-23 15:05:59',1,'question_theme','U',1,'','Text questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"text-huge\"}'),
(17,'language','Y','application/views/survey/questions/answer/language','/assets/images/screenshots/I.png','Language switch','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Language switch question type configuration','2019-09-23 15:05:59',1,'question_theme','I',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"0\",\"assessable\":\"0\",\"class\":\"language\"}'),
(18,'listradio','Y','application/views/survey/questions/answer/listradio','/assets/images/screenshots/L.png','List (Radio)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','List (radio) question type configuration','2019-09-23 15:05:59',1,'question_theme','L',1,'','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-radio\"}'),
(19,'list_dropdown','Y','application/views/survey/questions/answer/list_dropdown','/assets/images/screenshots/!.png','List (Dropdown)','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','List (dropdown) question type configuration','2019-09-23 15:05:59',1,'question_theme','!',1,'','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-dropdown\"}'),
(20,'list_with_comment','Y','application/views/survey/questions/answer/list_with_comment','/assets/images/screenshots/O.png','List with comment','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','List with comment question type configuration','2019-09-23 15:05:59',1,'question_theme','O',1,'','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-with-comment\"}'),
(21,'longfreetext','Y','application/views/survey/questions/answer/longfreetext','/assets/images/screenshots/T.png','Long free text','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Long free text question type configuration','2019-09-23 15:05:59',1,'question_theme','T',1,'','Text questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"text-long\"}'),
(22,'multiplechoice','Y','application/views/survey/questions/answer/multiplechoice','/assets/images/screenshots/M.png','Multiple choice','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Multiple choice question type configuration','2019-09-23 15:05:59',1,'question_theme','M',1,'','Multiple choice questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"multiple-opt\"}'),
(23,'multiplechoice_with_comments','Y','application/views/survey/questions/answer/multiplechoice_with_comments','/assets/images/screenshots/P.png','Multiple choice with comments','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Multiple choice with comments question type configuration','2019-09-23 15:05:59',1,'question_theme','P',1,'','Multiple choice questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"multiple-opt-comments\"}'),
(24,'multiplenumeric','Y','application/views/survey/questions/answer/multiplenumeric','/assets/images/screenshots/K.png','Multiple numerical input','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Multiple numerical input question type configuration','2019-09-23 15:05:59',1,'question_theme','K',1,'','Mask questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"numeric-multi\"}'),
(25,'multipleshorttext','Y','application/views/survey/questions/answer/multipleshorttext','/assets/images/screenshots/Q.png','Multiple short text','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Multiple short text question type configuration','2019-09-23 15:05:59',1,'question_theme','Q',1,'','Text questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"multiple-short-txt\"}'),
(26,'numerical','Y','application/views/survey/questions/answer/numerical','/assets/images/screenshots/N.png','Numerical input','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Numerical input question type configuration','2019-09-23 15:05:59',1,'question_theme','N',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"numeric\"}'),
(27,'ranking','Y','application/views/survey/questions/answer/ranking','/assets/images/screenshots/R.png','Ranking','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Ranking question type configuration','2019-09-23 15:05:59',1,'question_theme','R',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"ranking\"}'),
(28,'shortfreetext','Y','application/views/survey/questions/answer/shortfreetext','/assets/images/screenshots/S.png','Short free text','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Short free text question type configuration','2019-09-23 15:05:59',1,'question_theme','S',1,'','Text questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"text-short\"}'),
(29,'yesno','Y','application/views/survey/questions/answer/yesno','/assets/images/screenshots/Y.png','Yes/No','2018-09-08 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Yes/No question type configuration','2019-09-23 15:05:59',1,'question_theme','Y',1,'','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"yes-no\"}'),
(30,'bootstrap_dropdown','Y','themes/question/bootstrap_dropdown/survey/questions/answer/list_dropdown','/themes/question/bootstrap_dropdown/survey/questions/answer/list_dropdown/assets/bootstrap_dropdown_list_dropdown.png','Bootstrap dropdown','1970-01-01 01:00:00','Adam Zammit','adam.zammit@acspri.org.au','https://www.acspri.org.au','Copyright (C) 2021 The Australian Consortium for Social and Political Research Incorporated (ACSPRI)','GNU General Public License version 2 or later','1.0','1','Bootstrap dropdown theme','2021-09-29 12:00:00',1,'question_theme','!',1,'!','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-dropdown\"}'),
(31,'bootstrap_buttons','Y','themes/question/bootstrap_buttons/survey/questions/answer/listradio','/themes/question/bootstrap_buttons/survey/questions/answer/listradio/assets/bootstrap_buttons_listradio.png','Bootstrap buttons','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','New implementation of the Bootstrap buttons question theme','2019-09-23 15:05:59',1,'question_theme','L',1,'L','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-radio\"}'),
(32,'bootstrap_buttons_multi','Y','themes/question/bootstrap_buttons_multi/survey/questions/answer/multiplechoice','/themes/question/bootstrap_buttons_multi/survey/questions/answer/multiplechoice/assets/bootstrap_buttons_multiplechoice.png','Bootstrap buttons','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2018 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','New implementation of the Bootstrap buttons question theme','2019-09-23 15:05:59',1,'question_theme','M',1,'M','Multiple choice questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"multiple-opt\"}'),
(33,'browserdetect','Y','themes/question/browserdetect/survey/questions/answer/shortfreetext','themes/question/browserdetect/survey/questions/answer/shortfreetext/assets/browserdetect.png','Browser detection','2017-07-09 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2017 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Browser, Platform and Proxy detection','2019-09-23 15:05:59',1,'question_theme','S',1,'S','Text questions','{\"subquestions\":\"0\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"text-short\"}'),
(34,'image_select-listradio','Y','themes/question/image_select-listradio/survey/questions/answer/listradio','themes/question/image_select-listradio/survey/questions/answer/listradio/assets/image_select_listradio.png','Image select list (Radio)','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2016 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','List Radio with images.','2019-09-23 15:05:59',1,'question_theme','L',1,'L','Single choice questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"list-radio\"}'),
(35,'image_select-multiplechoice','Y','themes/question/image_select-multiplechoice/survey/questions/answer/multiplechoice','themes/question/image_select-multiplechoice/survey/questions/answer/multiplechoice/assets/image_select_multiplechoice.png','Image select multiple choice','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2016 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Multiplechoice with images.','2019-09-23 15:05:59',1,'question_theme','M',1,'M','Multiple choice questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"1\",\"class\":\"multiple-opt\"}'),
(36,'inputondemand','Y','themes/question/inputondemand/survey/questions/answer/multipleshorttext','themes/question/inputondemand/survey/questions/answer/multipleshorttext/assets/inputondemand.png','Input on demand','2019-10-04 00:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2019 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','Hide not needed input fields in multiple shorttext','2019-09-23 15:05:59',1,'question_theme','Q',1,'Q','Text questions','{\"subquestions\":\"1\",\"answerscales\":\"0\",\"hasdefaultvalues\":\"1\",\"assessable\":\"0\",\"class\":\"multiple-short-txt\"}'),
(37,'ranking_advanced','Y','themes/question/ranking_advanced/survey/questions/answer/ranking','themes/question/ranking_advanced/survey/questions/answer/ranking/assets/advanced_ranking.png','Ranking advanced','1970-01-01 01:00:00','LimeSurvey GmbH','info@limesurvey.org','http://www.limesurvey.org','Copyright (C) 2005 - 2017 LimeSurvey Gmbh, Inc. All rights reserved.','GNU General Public License version 2 or later','1.0','1','New implementation of the ranking question','2019-09-23 15:05:59',1,'question_theme','R',1,'R','Mask questions','{\"subquestions\":\"0\",\"answerscales\":\"1\",\"hasdefaultvalues\":\"0\",\"assessable\":\"1\",\"class\":\"ranking\"}');
/*!40000 ALTER TABLE `lime_question_themes` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_questions` (
  `qid` int(11) NOT NULL AUTO_INCREMENT,
  `parent_qid` int(11) NOT NULL DEFAULT 0,
  `sid` int(11) NOT NULL DEFAULT 0,
  `gid` int(11) NOT NULL DEFAULT 0,
  `type` varchar(30) NOT NULL DEFAULT 'T',
  `title` varchar(20) NOT NULL DEFAULT '',
  `preg` text DEFAULT NULL,
  `other` varchar(1) NOT NULL DEFAULT 'N',
  `mandatory` varchar(1) DEFAULT NULL,
  `encrypted` varchar(1) DEFAULT 'N',
  `question_order` int(11) NOT NULL,
  `scale_id` int(11) NOT NULL DEFAULT 0,
  `same_default` int(11) NOT NULL DEFAULT 0,
  `relevance` text DEFAULT NULL,
  `question_theme_name` varchar(150) DEFAULT NULL,
  `modulename` varchar(255) DEFAULT NULL,
  `same_script` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`qid`),
  KEY `lime_idx1_questions` (`sid`),
  KEY `lime_idx2_questions` (`gid`),
  KEY `lime_idx3_questions` (`type`),
  KEY `lime_idx4_questions` (`title`),
  KEY `lime_idx5_questions` (`parent_qid`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_questions` WRITE;
/*!40000 ALTER TABLE `lime_questions` DISABLE KEYS */;
INSERT INTO `lime_questions` VALUES
(1,0,186734,1,'Y','q1','','N','N','N',1,0,0,'1','yesno',NULL,0),
(2,0,186734,1,'T','q2','','N','N','N',2,0,0,'q1.NAOK == \"Y\"','longfreetext','',0);
/*!40000 ALTER TABLE `lime_questions` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_quota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_quota` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `qlimit` int(11) DEFAULT NULL,
  `action` int(11) DEFAULT NULL,
  `active` int(11) NOT NULL DEFAULT 1,
  `autoload_url` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_quota` (`sid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_quota` WRITE;
/*!40000 ALTER TABLE `lime_quota` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_quota` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_quota_languagesettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_quota_languagesettings` (
  `quotals_id` int(11) NOT NULL AUTO_INCREMENT,
  `quotals_quota_id` int(11) NOT NULL DEFAULT 0,
  `quotals_language` varchar(45) NOT NULL DEFAULT 'en',
  `quotals_name` varchar(255) DEFAULT NULL,
  `quotals_message` mediumtext NOT NULL,
  `quotals_url` varchar(255) DEFAULT NULL,
  `quotals_urldescrip` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`quotals_id`),
  KEY `lime_idx1_quota_id` (`quotals_quota_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_quota_languagesettings` WRITE;
/*!40000 ALTER TABLE `lime_quota_languagesettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_quota_languagesettings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_quota_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_quota_members` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) DEFAULT NULL,
  `qid` int(11) DEFAULT NULL,
  `quota_id` int(11) DEFAULT NULL,
  `code` varchar(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_idx1_quota_members` (`sid`,`qid`,`quota_id`,`code`),
  KEY `lime_idx2_quota_id` (`quota_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_quota_members` WRITE;
/*!40000 ALTER TABLE `lime_quota_members` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_quota_members` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_saved_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_saved_control` (
  `scid` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) NOT NULL DEFAULT 0,
  `srid` int(11) NOT NULL DEFAULT 0,
  `identifier` text NOT NULL,
  `access_code` text NOT NULL,
  `email` varchar(192) DEFAULT NULL,
  `ip` text NOT NULL,
  `saved_thisstep` text NOT NULL,
  `status` varchar(1) NOT NULL DEFAULT '',
  `saved_date` datetime NOT NULL,
  `refurl` text DEFAULT NULL,
  PRIMARY KEY (`scid`),
  KEY `lime_idx1_saved_control` (`sid`),
  KEY `lime_idx2_saved_control` (`srid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_saved_control` WRITE;
/*!40000 ALTER TABLE `lime_saved_control` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_saved_control` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_sessions` (
  `id` varchar(32) NOT NULL,
  `expire` int(11) DEFAULT NULL,
  `data` longblob DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sess_expire` (`expire`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_sessions` WRITE;
/*!40000 ALTER TABLE `lime_sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_sessions` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_settings_global`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_settings_global` (
  `stg_name` varchar(50) NOT NULL DEFAULT '',
  `stg_value` mediumtext NOT NULL,
  PRIMARY KEY (`stg_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_settings_global` WRITE;
/*!40000 ALTER TABLE `lime_settings_global` DISABLE KEYS */;
INSERT INTO `lime_settings_global` VALUES
('sendadmincreationemail','1'),
('admincreationemailsubject','User registration at \'{SITENAME}\''),
('admincreationemailtemplate','<p>Hello {FULLNAME}, </p><p>This is an automated email notification that a user has been created for you on the website <strong>\'{SITENAME}\'</strong>.</p><p></p><p>You can use now the following credentials to log in:</p><p><strong>Username</strong>: {USERNAME}</p><p><a href=\"{LOGINURL}\">Click here to set your password</a></p><p>If you have any questions regarding this email, please do not hesitate to contact the site administrator at {SITEADMINEMAIL}.</p><p> </p><p>Thank you!</p>'),
('DBVersion','651');
/*!40000 ALTER TABLE `lime_settings_global` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_settings_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_settings_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` int(11) NOT NULL,
  `entity` varchar(15) DEFAULT NULL,
  `entity_id` varchar(31) DEFAULT NULL,
  `stg_name` varchar(63) NOT NULL,
  `stg_value` mediumtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_settings_user` (`uid`),
  KEY `lime_idx2_settings_user` (`entity`),
  KEY `lime_idx3_settings_user` (`entity_id`),
  KEY `lime_idx4_settings_user` (`stg_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_settings_user` WRITE;
/*!40000 ALTER TABLE `lime_settings_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_settings_user` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_source_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_source_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `category` varchar(35) DEFAULT NULL,
  `message` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_source_message` WRITE;
/*!40000 ALTER TABLE `lime_source_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_source_message` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_survey_links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_survey_links` (
  `participant_id` varchar(50) NOT NULL,
  `token_id` int(11) NOT NULL,
  `survey_id` int(11) NOT NULL,
  `date_created` datetime DEFAULT NULL,
  `date_invited` datetime DEFAULT NULL,
  `date_completed` datetime DEFAULT NULL,
  PRIMARY KEY (`participant_id`,`token_id`,`survey_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_survey_links` WRITE;
/*!40000 ALTER TABLE `lime_survey_links` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_survey_links` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_survey_url_parameters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_survey_url_parameters` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sid` int(11) NOT NULL,
  `parameter` varchar(50) NOT NULL,
  `targetqid` int(11) DEFAULT NULL,
  `targetsqid` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_survey_url_parameters` WRITE;
/*!40000 ALTER TABLE `lime_survey_url_parameters` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_survey_url_parameters` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveymenu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveymenu` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parent_id` int(11) DEFAULT NULL,
  `survey_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `ordering` int(11) DEFAULT 0,
  `level` int(11) DEFAULT 0,
  `title` varchar(168) NOT NULL DEFAULT '',
  `position` varchar(192) NOT NULL DEFAULT 'side',
  `description` text DEFAULT NULL,
  `showincollapse` int(11) DEFAULT 0,
  `active` int(11) NOT NULL DEFAULT 0,
  `changed_at` datetime DEFAULT NULL,
  `changed_by` int(11) NOT NULL DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `created_by` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_surveymenu_name` (`name`),
  KEY `lime_idx2_surveymenu` (`title`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveymenu` WRITE;
/*!40000 ALTER TABLE `lime_surveymenu` DISABLE KEYS */;
INSERT INTO `lime_surveymenu` VALUES
(1,NULL,NULL,NULL,'settings',1,0,'Survey settings','side','Survey settings',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(2,NULL,NULL,NULL,'mainmenu',2,0,'Survey menu','side','Main survey menu',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(3,NULL,NULL,NULL,'quickmenu',3,0,'Quick menu','collapsed','Quick menu',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0);
/*!40000 ALTER TABLE `lime_surveymenu` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveymenu_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveymenu_entries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `menu_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `ordering` int(11) DEFAULT 0,
  `name` varchar(168) DEFAULT '',
  `title` varchar(168) NOT NULL DEFAULT '',
  `menu_title` varchar(168) NOT NULL DEFAULT '',
  `menu_description` text DEFAULT NULL,
  `menu_icon` varchar(192) NOT NULL DEFAULT '',
  `menu_icon_type` varchar(192) NOT NULL DEFAULT '',
  `menu_class` varchar(192) NOT NULL DEFAULT '',
  `menu_link` varchar(192) NOT NULL DEFAULT '',
  `action` varchar(192) NOT NULL DEFAULT '',
  `template` varchar(192) NOT NULL DEFAULT '',
  `partial` varchar(192) NOT NULL DEFAULT '',
  `classes` varchar(192) NOT NULL DEFAULT '',
  `permission` varchar(192) NOT NULL DEFAULT '',
  `permission_grade` varchar(192) DEFAULT NULL,
  `data` mediumtext DEFAULT NULL,
  `getdatamethod` varchar(192) NOT NULL DEFAULT '',
  `language` varchar(32) NOT NULL DEFAULT 'en-GB',
  `showincollapse` int(11) DEFAULT 0,
  `active` int(11) NOT NULL DEFAULT 0,
  `changed_at` datetime DEFAULT NULL,
  `changed_by` int(11) NOT NULL DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `created_by` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lime_surveymenu_entries_name` (`name`),
  KEY `lime_idx1_surveymenu_entries` (`menu_id`),
  KEY `lime_idx5_surveymenu_entries` (`menu_title`)
) ENGINE=MyISAM AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveymenu_entries` WRITE;
/*!40000 ALTER TABLE `lime_surveymenu_entries` DISABLE KEYS */;
INSERT INTO `lime_surveymenu_entries` VALUES
(1,1,NULL,1,'overview','Survey overview','Overview','Open the general survey overview','ri-bar-chart-horizontal-line','remix','','surveyAdministration/view','','','','','','','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(2,1,NULL,2,'generalsettings','General survey settings','General','Open general survey settings','ri-tools-line','remix','','','updatesurveylocalesettings_generalsettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_generaloptions_panel','','surveysettings','read',NULL,'generalTabEditSurvey','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(3,1,NULL,3,'surveytexts','Survey text elements','Text elements','Survey text elements','ri-text-spacing','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/tab_edit_view','','surveylocale','read',NULL,'getTextEditData','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(4,1,NULL,4,'datasecurity','Privacy policy settings','Privacy policy','Edit privacy policy settings','ri-shield-line','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/tab_edit_view_datasecurity','','surveylocale','read',NULL,'getDataSecurityEditData','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(5,1,NULL,5,'theme_options','Theme options','Theme options','Edit theme options for this survey','ri-contrast-drop-fill','remix','','themeOptions/updateSurvey','','','','','surveysettings','update','{\"render\": {\"link\": { \"pjaxed\": true, \"data\": {\"surveyid\": [\"survey\",\"sid\"], \"gsid\":[\"survey\",\"gsid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(6,1,NULL,6,'presentation','Presentation & navigation settings','Presentation','Edit presentation and navigation settings','ri-slideshow-line','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_presentation_panel','','surveylocale','read',NULL,'tabPresentationNavigation','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(7,1,NULL,7,'tokens','Survey participant settings','Participant settings','Set additional options for survey participants','ri-body-scan-fill','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_tokens_panel','','surveylocale','read',NULL,'tabTokens','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(8,1,NULL,8,'notification','Notification and data management settings','Notifications & data','Edit settings for notification and data management','ri-notification-line','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_notification_panel','','surveylocale','read',NULL,'tabNotificationDataManagement','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(9,1,NULL,9,'publication','Publication & access control settings','Publication & access','Edit settings for publication and access control','ri-key-line','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_publication_panel','','surveylocale','read',NULL,'tabPublicationAccess','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(10,1,NULL,10,'surveypermissions','Edit survey permissions','Survey permissions','Edit permissions for this survey','ri-lock-password-line','remix','','surveyPermissions/index','','','','','surveysecurity','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(11,2,NULL,1,'listQuestions','Overview questions & groups','Overview questions & groups','Overview of questions and groups where you can add, edit and reorder them','','remix','','questionAdministration/listQuestions','','','','','surveycontent','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(12,2,NULL,4,'participants','Survey participants','Participants','Go to survey participant and token settings','','remix','','admin/tokens/sa/index/','','','','','tokens','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(13,2,NULL,5,'emailtemplates','Email templates','Email templates','Edit the templates for invitation, reminder and registration emails','','remix','','admin/emailtemplates/sa/index/','','','','','surveylocale','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(14,2,NULL,6,'failedemail','Failed email notifications','Failed email notifications','View and resend failed email notifications','','remix','','failedEmail/index/','','','','','surveylocale','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(15,2,NULL,7,'quotas','Edit quotas','Quotas','Edit quotas for this survey.','','remix','','quotas/index/','','','','','quotas','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(16,2,NULL,8,'assessments','Edit assessments','Assessments','Edit and look at the assessements for this survey.','','remix','','assessment/index','','','','','assessments','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(17,2,NULL,9,'panelintegration','Edit survey panel integration','Panel integration','Define panel integrations for your survey','','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_integration_panel','','surveylocale','read','{\"render\": {\"link\": { \"pjaxed\": false}}}','tabPanelIntegration','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(18,2,NULL,10,'responses','Responses','Responses','Responses','','remix','','responses/browse/','','','','','responses','read','{\"render\": {\"isActive\": true, \"link\": {\"data\": {\"surveyId\": [\"survey\", \"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(19,2,NULL,11,'statistics','Statistics','Statistics','Statistics','','remix','','admin/statistics/sa/simpleStatistics/','','','','','statistics','read','{\"render\": {\"isActive\": true, \"link\": {\"data\": {\"surveyid\": [\"survey\", \"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(20,2,NULL,12,'resources','Add/edit resources (files/images) for this survey','Resources','Add/edit resources (files/images) for this survey','','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_resources_panel','','surveylocale','read','{\"render\": { \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','tabResourceManagement','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(21,2,NULL,13,'plugins','Simple plugin settings','Simple plugins','Edit simple plugin settings','','remix','','','updatesurveylocalesettings','editLocalSettings_main_view','/admin/survey/subview/accordion/_plugins_panel','','surveysettings','read','{\"render\": {\"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','pluginTabSurvey','en-GB',0,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(22,3,NULL,1,'activateSurvey','Activate survey','Activate survey','Activate survey','ri-play-fill','remix','','surveyAdministration/activate','','','','','surveyactivation','update','{\"render\": {\"isActive\": false, \"link\": {\"data\": {\"iSurveyID\": [\"survey\",\"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(23,3,NULL,2,'deactivateSurvey','Stop survey','Stop survey','Stop this survey','ri-stop-fill','remix','','surveyAdministration/deactivate','','','','','surveyactivation','update','{\"render\": {\"isActive\": true, \"link\": {\"data\": {\"surveyid\": [\"survey\",\"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(24,3,NULL,3,'testSurvey','Go to survey','Go to survey','Go to survey','ri-settings-5-fill','remix','','survey/index/','','','','','','','{\"render\": {\"link\": {\"external\": true, \"data\": {\"sid\": [\"survey\",\"sid\"], \"newtest\": \"Y\", \"lang\": [\"survey\",\"language\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(25,3,NULL,4,'surveyLogicFile','Survey logic file','Survey logic file','Survey logic file','ri-git-branch-fill','remix','','admin/expressions/sa/survey_logic_file/','','','','','surveycontent','read','{\"render\": { \"link\": {\"data\": {\"sid\": [\"survey\",\"sid\"]}}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0),
(26,3,NULL,5,'cpdb','Central participant database','Central participant database','Central participant database','ri-group-fill','remix','','admin/participants/sa/displayParticipants','','','','','tokens','read','{\"render\": {\"link\": {}}}','','en-GB',1,1,'2026-10-18 19:51:30',0,'2026-10-18 19:51:30',0);
/*!40000 ALTER TABLE `lime_surveymenu_entries` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveys` (
  `sid` int(11) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `gsid` int(11) DEFAULT 1,
  `admin` varchar(50) DEFAULT NULL,
  `active` varchar(1) NOT NULL DEFAULT 'N',
  `expires` datetime DEFAULT NULL,
  `startdate` datetime DEFAULT NULL,
  `adminemail` varchar(254) DEFAULT NULL,
  `anonymized` varchar(1) NOT NULL DEFAULT 'N',
  `format` varchar(1) DEFAULT NULL,
  `savetimings` varchar(1) NOT NULL DEFAULT 'N',
  `template` varchar(100) DEFAULT 'default',
  `language` varchar(50) DEFAULT NULL,
  `additional_languages` text DEFAULT NULL,
  `datestamp` varchar(1) NOT NULL DEFAULT 'Y',
  `usecookie` varchar(1) NOT NULL DEFAULT 'N',
  `allowregister` varchar(1) NOT NULL DEFAULT 'N',
  `allowsave` varchar(1) NOT NULL DEFAULT 'Y',
  `autonumber_start` int(11) NOT NULL DEFAULT 0,
  `autoredirect` varchar(1) NOT NULL DEFAULT 'N',
  `allowprev` varchar(1) NOT NULL DEFAULT 'N',
  `printanswers` varchar(1) NOT NULL DEFAULT 'N',
  `ipaddr` varchar(1) NOT NULL DEFAULT 'N',
  `ipanonymize` varchar(1) NOT NULL DEFAULT 'N',
  `refurl` varchar(1) NOT NULL DEFAULT 'N',
  `datecreated` datetime DEFAULT NULL,
  `showsurveypolicynotice` int(11) DEFAULT 0,
  `showregisterpolicy` varchar(1) NOT NULL DEFAULT 'I',
  `showtokenpolicy` varchar(1) NOT NULL DEFAULT 'I',
  `publicstatistics` varchar(1) NOT NULL DEFAULT 'N',
  `publicgraphs` varchar(1) NOT NULL DEFAULT 'N',
  `listpublic` varchar(1) NOT NULL DEFAULT 'N',
  `htmlemail` varchar(1) NOT NULL DEFAULT 'Y',
  `sendconfirmation` varchar(1) NOT NULL DEFAULT 'Y',
  `tokenanswerspersistence` varchar(1) NOT NULL DEFAULT 'N',
  `assessments` varchar(1) NOT NULL DEFAULT 'N',
  `usecaptcha` varchar(1) NOT NULL DEFAULT 'N',
  `usetokens` varchar(1) NOT NULL DEFAULT 'N',
  `bounce_email` varchar(254) DEFAULT NULL,
  `attributedescriptions` mediumtext DEFAULT NULL,
  `emailresponseto` text DEFAULT NULL,
  `emailnotificationto` text DEFAULT NULL,
  `tokenlength` int(11) NOT NULL DEFAULT 15,
  `showxquestions` varchar(1) DEFAULT 'Y',
  `showgroupinfo` varchar(1) DEFAULT 'B',
  `shownoanswer` varchar(1) DEFAULT 'Y',
  `showqnumcode` varchar(1) DEFAULT 'X',
  `bouncetime` int(11) DEFAULT NULL,
  `bounceprocessing` varchar(1) DEFAULT 'N',
  `bounceaccounttype` varchar(4) DEFAULT NULL,
  `bounceaccounthost` varchar(200) DEFAULT NULL,
  `bounceaccountpass` text DEFAULT NULL,
  `bounceaccountencryption` varchar(3) DEFAULT NULL,
  `bounceaccountuser` varchar(200) DEFAULT NULL,
  `showwelcome` varchar(1) DEFAULT 'Y',
  `showprogress` varchar(1) DEFAULT 'Y',
  `questionindex` int(11) NOT NULL DEFAULT 0,
  `navigationdelay` int(11) NOT NULL DEFAULT 0,
  `nokeyboard` varchar(1) DEFAULT 'N',
  `alloweditaftercompletion` varchar(1) DEFAULT 'N',
  `googleanalyticsstyle` varchar(1) DEFAULT NULL,
  `googleanalyticsapikey` varchar(25) DEFAULT NULL,
  `tokenencryptionoptions` text DEFAULT NULL,
  `access_mode` varchar(1) DEFAULT 'O',
  `lastmodified` datetime NOT NULL,
  PRIMARY KEY (`sid`),
  KEY `lime_idx1_surveys` (`owner_id`),
  KEY `lime_idx2_surveys` (`gsid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveys` WRITE;
/*!40000 ALTER TABLE `lime_surveys` DISABLE KEYS */;
INSERT INTO `lime_surveys` VALUES
(186734,1,1,'','N',NULL,'1970-01-01 02:00:00','','N','S','N','fruity_twentythree','en','','N','N','Y','Y',0,'N','Y','N','N','N','N','2026-10-18 19:51:31',0,'I','I','N','N','N','Y','Y','N','N','N','Y','',NULL,'','',15,'Y','B','N','X',NULL,'N',NULL,NULL,NULL,NULL,NULL,'N','Y',0,0,'N','N',NULL,NULL,'','O','2026-10-18 19:51:31');
/*!40000 ALTER TABLE `lime_surveys` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveys_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveys_groups` (
  `gsid` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `template` varchar(128) DEFAULT 'default',
  `description` text DEFAULT NULL,
  `sortorder` int(11) NOT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `alwaysavailable` tinyint(1) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `modified` datetime DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  PRIMARY KEY (`gsid`),
  KEY `lime_idx1_surveys_groups` (`name`),
  KEY `lime_idx2_surveys_groups` (`title`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveys_groups` WRITE;
/*!40000 ALTER TABLE `lime_surveys_groups` DISABLE KEYS */;
INSERT INTO `lime_surveys_groups` VALUES
(1,'default','Default',NULL,'Default survey group',0,1,NULL,NULL,'2026-10-18 19:51:30','2026-10-18 19:51:30',1);
/*!40000 ALTER TABLE `lime_surveys_groups` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveys_groupsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveys_groupsettings` (
  `gsid` int(11) NOT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `admin` varchar(50) DEFAULT NULL,
  `adminemail` varchar(254) DEFAULT NULL,
  `anonymized` varchar(1) NOT NULL DEFAULT 'N',
  `format` varchar(1) DEFAULT NULL,
  `savetimings` varchar(1) NOT NULL DEFAULT 'N',
  `template` varchar(100) DEFAULT 'default',
  `datestamp` varchar(1) NOT NULL DEFAULT 'Y',
  `usecookie` varchar(1) NOT NULL DEFAULT 'N',
  `allowregister` varchar(1) NOT NULL DEFAULT 'N',
  `allowsave` varchar(1) NOT NULL DEFAULT 'Y',
  `autonumber_start` int(11) DEFAULT 0,
  `autoredirect` varchar(1) NOT NULL DEFAULT 'N',
  `allowprev` varchar(1) NOT NULL DEFAULT 'N',
  `printanswers` varchar(1) NOT NULL DEFAULT 'N',
  `ipaddr` varchar(1) NOT NULL DEFAULT 'N',
  `ipanonymize` varchar(1) NOT NULL DEFAULT 'N',
  `refurl` varchar(1) NOT NULL DEFAULT 'N',
  `showsurveypolicynotice` int(11) DEFAULT 0,
  `showregisterpolicy` varchar(1) NOT NULL DEFAULT 'I',
  `showtokenpolicy` varchar(1) NOT NULL DEFAULT 'I',
  `publicstatistics` varchar(1) NOT NULL DEFAULT 'N',
  `publicgraphs` varchar(1) NOT NULL DEFAULT 'N',
  `listpublic` varchar(1) NOT NULL DEFAULT 'N',
  `htmlemail` varchar(1) NOT NULL DEFAULT 'Y',
  `sendconfirmation` varchar(1) NOT NULL DEFAULT 'Y',
  `tokenanswerspersistence` varchar(1) NOT NULL DEFAULT 'N',
  `assessments` varchar(1) NOT NULL DEFAULT 'N',
  `usecaptcha` varchar(1) NOT NULL DEFAULT 'N',
  `bounce_email` varchar(254) DEFAULT NULL,
  `attributedescriptions` text DEFAULT NULL,
  `emailresponseto` text DEFAULT NULL,
  `emailnotificationto` text DEFAULT NULL,
  `tokenlength` int(11) DEFAULT 15,
  `showxquestions` varchar(1) DEFAULT 'Y',
  `showgroupinfo` varchar(1) DEFAULT 'B',
  `shownoanswer` varchar(1) DEFAULT 'Y',
  `showqnumcode` varchar(1) DEFAULT 'X',
  `showwelcome` varchar(1) DEFAULT 'Y',
  `showprogress` varchar(1) DEFAULT 'Y',
  `questionindex` int(11) DEFAULT 0,
  `navigationdelay` int(11) DEFAULT 0,
  `nokeyboard` varchar(1) DEFAULT 'N',
  `alloweditaftercompletion` varchar(1) DEFAULT 'N',
  PRIMARY KEY (`gsid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveys_groupsettings` WRITE;
/*!40000 ALTER TABLE `lime_surveys_groupsettings` DISABLE KEYS */;
INSERT INTO `lime_surveys_groupsettings` VALUES
(0,1,'Administrator','your-email@example.net','N','G','N','fruity_twentythree','Y','N','N','Y',0,'N','N','N','N','N','N',0,'N','N','N','N','N','Y','Y','N','N','N',NULL,NULL,NULL,NULL,15,'Y','B','Y','X','Y','Y',0,0,'N','N'),
(1,-1,'inherit','inherit','I','I','I','inherit','I','I','I','I',0,'I','I','I','I','I','I',0,'I','I','I','I','I','I','I','I','I','E','inherit',NULL,'inherit','inherit',-1,'I','I','I','I','I','I',-1,-1,'I','I');
/*!40000 ALTER TABLE `lime_surveys_groupsettings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_surveys_languagesettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_surveys_languagesettings` (
  `surveyls_survey_id` int(11) NOT NULL,
  `surveyls_language` varchar(45) NOT NULL DEFAULT 'en',
  `surveyls_title` varchar(200) NOT NULL,
  `surveyls_description` mediumtext DEFAULT NULL,
  `surveyls_welcometext` mediumtext DEFAULT NULL,
  `surveyls_endtext` mediumtext DEFAULT NULL,
  `surveyls_policy_notice` mediumtext DEFAULT NULL,
  `surveyls_policy_error` text DEFAULT NULL,
  `surveyls_policy_notice_label` varchar(192) DEFAULT NULL,
  `surveyls_url` text DEFAULT NULL,
  `surveyls_urldescription` varchar(255) DEFAULT NULL,
  `surveyls_email_invite_subj` varchar(255) DEFAULT NULL,
  `surveyls_email_invite` mediumtext DEFAULT NULL,
  `surveyls_email_remind_subj` varchar(255) DEFAULT NULL,
  `surveyls_email_remind` mediumtext DEFAULT NULL,
  `surveyls_email_register_subj` varchar(255) DEFAULT NULL,
  `surveyls_email_register` mediumtext DEFAULT NULL,
  `surveyls_email_confirm_subj` varchar(255) DEFAULT NULL,
  `surveyls_email_confirm` mediumtext DEFAULT NULL,
  `surveyls_dateformat` int(11) NOT NULL DEFAULT 1,
  `surveyls_attributecaptions` text DEFAULT NULL,
  `surveyls_alias` varchar(100) DEFAULT NULL,
  `email_admin_notification_subj` varchar(255) DEFAULT NULL,
  `email_admin_notification` mediumtext DEFAULT NULL,
  `email_admin_responses_subj` varchar(255) DEFAULT NULL,
  `email_admin_responses` mediumtext DEFAULT NULL,
  `surveyls_numberformat` int(11) NOT NULL DEFAULT 0,
  `attachments` text DEFAULT NULL,
  PRIMARY KEY (`surveyls_survey_id`,`surveyls_language`),
  KEY `lime_idx1_surveys_languagesettings` (`surveyls_title`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_surveys_languagesettings` WRITE;
/*!40000 ALTER TABLE `lime_surveys_languagesettings` DISABLE KEYS */;
INSERT INTO `lime_surveys_languagesettings` VALUES
(186734,'en','Test screen out','','','','','','','','','Invitation to participate in a survey','Dear {FIRSTNAME},<br />\n<br />\nyou have been invited to participate in a survey.<br />\n<br />\nThe survey is titled:<br />\n\"{SURVEYNAME}\"<br />\n<br />\n\"{SURVEYDESCRIPTION}\"<br />\n<br />\nTo participate, please click on the link below.<br />\n<br />\nSincerely,<br />\n<br />\n{ADMINNAME} ({ADMINEMAIL})<br />\n<br />\n----------------------------------------------<br />\nClick here to do the survey:<br />\n{SURVEYURL}<br />\n<br />\nIf you do not want to participate in this survey and don\'t want to receive any more invitations please click the following link:<br />\n{OPTOUTURL}<br />\n<br />\nIf you are blacklisted but want to participate in this survey and want to receive invitations please click the following link:<br />\n{OPTINURL}','Reminder to participate in a survey','Dear {FIRSTNAME},<br />\n<br />\nRecently we invited you to participate in a survey.<br />\n<br />\nWe note that you have not yet completed the survey, and wish to remind you that the survey is still available should you wish to take part.<br />\n<br />\nThe survey is titled:<br />\n\"{SURVEYNAME}\"<br />\n<br />\n\"{SURVEYDESCRIPTION}\"<br />\n<br />\nTo participate, please click on the link below.<br />\n<br />\nSincerely,<br />\n<br />\n{ADMINNAME} ({ADMINEMAIL})<br />\n<br />\n----------------------------------------------<br />\nClick here to do the survey:<br />\n{SURVEYURL}<br />\n<br />\nIf you do not want to participate in this survey and don\'t want to receive any more invitations please click the following link:<br />\n{OPTOUTURL}','Survey registration confirmation','Dear {FIRSTNAME},<br />\n<br />\nYou, or someone using your email address, have registered to participate in an online survey titled {SURVEYNAME}.<br />\n<br />\nTo complete this survey, click on the following URL:<br />\n<br />\n{SURVEYURL}<br />\n<br />\nIf you have any questions about this survey, or if you did not register to participate and believe this email is in error, please contact {ADMINNAME} at {ADMINEMAIL}.','Confirmation of your participation in our survey','Dear {FIRSTNAME},<br />\n<br />\nthis email is to confirm that you have completed the survey titled {SURVEYNAME} and your response has been saved. Thank you for participating.<br />\n<br />\nIf you have any further questions about this email, please contact {ADMINNAME} on {ADMINEMAIL}.<br />\n<br />\nSincerely,<br />\n<br />\n{ADMINNAME}',1,NULL,'','Response submission for survey {SURVEYNAME}','Hello,<br />\n<br />\nA new response was submitted for your survey \'{SURVEYNAME}\'.<br />\n<br />\nClick the following link to reload the survey:<br />\n{RELOADURL}<br />\n<br />\nClick the following link to see the individual response:<br />\n{VIEWRESPONSEURL}<br />\n<br />\nClick the following link to edit the individual response:<br />\n{EDITRESPONSEURL}<br />\n<br />\nView statistics by clicking here:<br />\n{STATISTICSURL}','Response submission for survey {SURVEYNAME} with results','Hello,<br />\n<br />\nA new response was submitted for your survey \'{SURVEYNAME}\'.<br />\n<br />\nClick the following link to reload the survey:<br />\n{RELOADURL}<br />\n<br />\nClick the following link to see the individual response:<br />\n{VIEWRESPONSEURL}<br />\n<br />\nClick the following link to edit the individual response:<br />\n{EDITRESPONSEURL}<br />\n<br />\nView statistics by clicking here:<br />\n{STATISTICSURL}<br />\n<br />\n<br />\nThe following answers were given by the participant:<br />\n{ANSWERTABLE}',0,NULL);
/*!40000 ALTER TABLE `lime_surveys_languagesettings` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_template_configuration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_template_configuration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `template_name` varchar(150) NOT NULL,
  `sid` int(11) DEFAULT NULL,
  `gsid` int(11) DEFAULT NULL,
  `uid` int(11) DEFAULT NULL,
  `files_css` text DEFAULT NULL,
  `files_js` text DEFAULT NULL,
  `files_print_css` text DEFAULT NULL,
  `options` text DEFAULT NULL,
  `cssframework_name` varchar(45) DEFAULT NULL,
  `cssframework_css` mediumtext DEFAULT NULL,
  `cssframework_js` mediumtext DEFAULT NULL,
  `packages_to_load` text DEFAULT NULL,
  `packages_ltr` text DEFAULT NULL,
  `packages_rtl` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_template_configuration` (`template_name`),
  KEY `lime_idx2_template_configuration` (`sid`),
  KEY `lime_idx3_template_configuration` (`gsid`),
  KEY `lime_idx4_template_configuration` (`uid`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_template_configuration` WRITE;
/*!40000 ALTER TABLE `lime_template_configuration` DISABLE KEYS */;
INSERT INTO `lime_template_configuration` VALUES
(1,'vanilla',NULL,NULL,NULL,'{\"add\":[\"css/base.css\",\"css/theme.css\",\"css/noTablesOnMobile.css\",\"css/custom.css\"]}','{\"add\":[\"scripts/theme.js\",\"scripts/ajaxify.js\",\"scripts/custom.js\"]}','{\"add\":[\"css/print_theme.css\"]}','{\"ajaxmode\":\"off\", \"animatebody\":\"off\", \"fixnumauto\":\"enable\",\"brandlogo\":\"on\",\"container\":\"on\", \"hideprivacyinfo\": \"off\", \"brandlogofile\":\"themes/survey/vanilla/files/logo.png\",\"font\":\"noto\", \"showpopups\":\"1\", \"showclearall\":\"off\", \"questionhelptextposition\":\"top\"}','bootstrap','{}','','{\"add\":[\"pjax\",\"font-noto\",\"moment\"]}',NULL,NULL),
(2,'fruity',NULL,NULL,NULL,'{\"add\":[\"css/ajaxify.css\",\"css/animate.css\",\"css/variations/sea_green.css\",\"css/theme.css\",\"css/custom.css\"]}','{\"add\":[\"scripts/theme.js\",\"scripts/ajaxify.js\",\"scripts/custom.js\"]}','{\"add\":[\"css/print_theme.css\"]}','{\"ajaxmode\":\"off\",\"fixnumauto\":\"enable\",\"brandlogo\":\"on\",\"brandlogofile\":\"themes/survey/fruity/files/logo.png\",\"container\":\"on\",\"backgroundimage\":\"off\",\"backgroundimagefile\":null,\"animatebody\":\"off\",\"bodyanimation\":\"fadeInRight\",\"bodyanimationduration\":\"500\",\"animatequestion\":\"off\",\"questionanimation\":\"flipInX\",\"questionanimationduration\":\"500\",\"animatealert\":\"off\",\"alertanimation\":\"shake\",\"alertanimationduration\":\"500\",\"font\":\"noto\",\"bodybackgroundcolor\":\"#ffffff\",\"fontcolor\":\"#444444\",\"questionbackgroundcolor\":\"#ffffff\",\"questionborder\":\"on\",\"questioncontainershadow\":\"on\",\"checkicon\":\"f00c\",\"animatecheckbox\":\"on\",\"checkboxanimation\":\"rubberBand\",\"checkboxanimationduration\":\"500\",\"animateradio\":\"on\",\"radioanimation\":\"zoomIn\",\"radioanimationduration\":\"500\",\"zebrastriping\":\"off\",\"stickymatrixheaders\":\"off\",\"greyoutselected\":\"off\",\"hideprivacyinfo\":\"off\",\"crosshover\":\"off\",\"showpopups\":\"1\", \"showclearall\":\"off\", \"questionhelptextposition\":\"top\",\"notables\":\"1\"}','bootstrap','{}','','{\"add\":[\"pjax\",\"font-noto\",\"moment\"]}',NULL,NULL),
(3,'bootswatch',NULL,NULL,NULL,'{\"add\":[\"css/ajaxify.css\",\"css/theme.css\",\"css/custom.css\"]}','{\"add\":[\"scripts/theme.js\",\"scripts/ajaxify.js\",\"scripts/custom.js\"]}','{\"add\":[\"css/print_theme.css\"]}','{\"ajaxmode\":\"off\",\"fixnumauto\":\"enable\",\"brandlogo\":\"on\",\"container\":\"on\",\"brandlogofile\":\"themes/survey/bootswatch/files/logo.png\", \"showpopups\":\"1\", \"showclearall\":\"off\", \"hideprivacyinfo\": \"off\", \"questionhelptextposition\":\"top\"}','bootstrap','{\"replace\":[[\"css/bootstrap.css\",\"css/variations/flatly.min.css\"]]}','','{\"add\":[\"pjax\",\"font-noto\",\"moment\"]}',NULL,NULL),
(4,'fruity_twentythree',NULL,NULL,NULL,'{\"add\":[\"css/variations/theme_apple.css\",\"css/base.css\",\"css/custom.css\"], \"remove\":[\"survey.css\", \"template-core.css\", \"awesome-bootstrap-checkbox/awesome-bootstrap-checkbox.css\", \"awesome-bootstrap-checkbox/awesome-bootstrap-checkbox-rtl.css\"]}','{\"add\":[\"scripts/theme.js\",\"scripts/custom.js\"], \"remove\":[\"survey.js\", \"template-core.js\"]}','{\"add\":[\"css/print_theme.css\"]}','{\"hideprivacyinfo\":\"off\",\"showpopups\":\"1\",\"showclearall\":\"off\",\"questionhelptextposition\":\"top\",\"fixnumauto\":\"enable\",\"backgroundimage\":\"off\",\"backgroundimagefile\":\".\\/files\\/pattern.png\",\"brandlogo\":\"off\",\"brandlogofile\":\"image::theme::files\\/logo.png\",\"font\":\"ibm-sans\", \"bodybackgroundcolor\":\"#ffffff\",\"fontcolor\":\"#444444\", \"questionbackgroundcolor\":\"#ffffff\", \"checkicon\":\"EB7A\",\"cssframework\":\"Apple\", \"notables\":\"1\"}','','','','{\"add\":[\"pjax\",\"moment\",\"font-ibm-sans\",\"font-ibm-serif\"]}',NULL,NULL),
(5,'fruity_twentythree',186734,NULL,NULL,'inherit','inherit','inherit','inherit','inherit','inherit','inherit','inherit',NULL,NULL),
(6,'fruity_twentythree',NULL,1,NULL,'inherit','inherit','inherit','inherit','inherit','inherit','inherit','inherit',NULL,NULL);
/*!40000 ALTER TABLE `lime_template_configuration` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `folder` varchar(45) DEFAULT NULL,
  `title` varchar(100) NOT NULL,
  `creation_date` datetime DEFAULT NULL,
  `author` varchar(150) DEFAULT NULL,
  `author_email` varchar(255) DEFAULT NULL,
  `author_url` varchar(255) DEFAULT NULL,
  `copyright` text DEFAULT NULL,
  `license` mediumtext DEFAULT NULL,
  `version` varchar(45) DEFAULT NULL,
  `api_version` varchar(45) NOT NULL,
  `view_folder` varchar(45) NOT NULL,
  `files_folder` varchar(45) NOT NULL,
  `description` mediumtext DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `extends` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lime_idx1_templates` (`name`),
  KEY `lime_idx2_templates` (`title`),
  KEY `lime_idx3_templates` (`owner_id`),
  KEY `lime_idx4_templates` (`extends`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_templates` WRITE;
/*!40000 ALTER TABLE `lime_templates` DISABLE KEYS */;
INSERT INTO `lime_templates` VALUES
(1,'vanilla','vanilla','Bootstrap Vanilla','2026-10-18 19:51:30','LimeSurvey GmbH','info@limesurvey.org','https://www.limesurvey.org/','Copyright (C) 2007-2019 The LimeSurvey Project Team\\r\\nAll rights reserved.','License: GNU/GPL License v2 or later, see LICENSE.php\\r\\n\\r\\nLimeSurvey is free software. This version may have been modified pursuant to the GNU General Public License, and as distributed it includes or is derivative of works licensed under the GNU General Public License or other free or open source software licenses. See COPYRIGHT.php for copyright notices and details.','3.0','3.0','views','files','A clean and simple base that can be used by developers to create their own Bootstrap based theme.',NULL,1,''),
(2,'fruity','fruity','Fruity','2026-10-18 19:51:30','LimeSurvey GmbH','info@limesurvey.org','https://www.limesurvey.org/','Copyright (C) 2007-2019 The LimeSurvey Project Team\\r\\nAll rights reserved.','License: GNU/GPL License v2 or later, see LICENSE.php\\r\\n\\r\\nLimeSurvey is free software. This version may have been modified pursuant to the GNU General Public License, and as distributed it includes or is derivative of works licensed under the GNU General Public License or other free or open source software licenses. See COPYRIGHT.php for copyright notices and details.','3.0','3.0','views','files','A fruity theme for a flexible use. This theme offers monochromes variations and many options for easy customizations.',NULL,1,'vanilla'),
(3,'bootswatch','bootswatch','Bootswatch','2026-10-18 19:51:30','LimeSurvey GmbH','info@limesurvey.org','https://www.limesurvey.org/','Copyright (C) 2007-2019 The LimeSurvey Project Team\\r\\nAll rights reserved.','License: GNU/GPL License v2 or later, see LICENSE.php\\r\\n\\r\\nLimeSurvey is free software. This version may have been modified pursuant to the GNU General Public License, and as distributed it includes or is derivative of works licensed under the GNU General Public License or other free or open source software licenses. See COPYRIGHT.php for copyright notices and details.','3.0','3.0','views','files','{{gT(\"Based on BootsWatch Themes:\")}}<br><a href=\'https://bootswatch.com/3/\' target=\'_blank\' rel=\'external\' title=\'{{gT(\"Visit Bootswatch page in a new window.\")}}\'>{{gT(\"Visit Bootswatch page\")}} <i class=\'ri-external-link-line\'></i><span class=\'visually-hidden\'>{{gT(\"(Opens in a new window)\")}}</span></a>',NULL,1,'vanilla'),
(4,'fruity_twentythree','fruity_twentythree','Fruity TwentyThree','2026-10-18 19:51:30','LimeSurvey GmbH','info@limesurvey.org','https://www.limesurvey.org/','Copyright (C) 2005 - 2023 LimeSurvey Gmbh, Inc. All rights reserved.','License: GNU/GPL License v2 or later, see LICENSE.php\\r\\n\\r\\nLimeSurvey is free software. This version may have been modified pursuant to the GNU General Public License, and as distributed it includes or is derivative of works licensed under the GNU General Public License or other free or open source software licenses. See COPYRIGHT.php for copyright notices and details.','1.0.0','3.0','views','files','Our default theme for a fruity and flexible use. This theme offers single color variations',NULL,1,'');
/*!40000 ALTER TABLE `lime_templates` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_tokens_186734`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_tokens_186734` (
  `tid` int(11) NOT NULL AUTO_INCREMENT,
  `participant_id` varchar(50) DEFAULT NULL,
  `firstname` text DEFAULT NULL,
  `lastname` text DEFAULT NULL,
  `email` text DEFAULT NULL,
  `emailstatus` text DEFAULT NULL,
  `token` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `language` varchar(25) DEFAULT NULL,
  `blacklisted` varchar(17) DEFAULT NULL,
  `sent` varchar(17) DEFAULT 'N',
  `remindersent` varchar(17) DEFAULT 'N',
  `remindercount` int(11) DEFAULT 0,
  `completed` varchar(17) DEFAULT 'N',
  `usesleft` int(11) DEFAULT 1,
  `validfrom` datetime DEFAULT NULL,
  `validuntil` datetime DEFAULT NULL,
  `mpid` int(11) DEFAULT NULL,
  PRIMARY KEY (`tid`),
  KEY `idx_token_token_186734_24431` (`token`),
  KEY `idx_email` (`email`(30))
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_tokens_186734` WRITE;
/*!40000 ALTER TABLE `lime_tokens_186734` DISABLE KEYS */;
INSERT INTO `lime_tokens_186734` VALUES
(1,NULL,'Pat','Participant','participant@example.org','OK','PARTTOKEN001','en',NULL,'N','N',0,'N',1,NULL,NULL,NULL);
/*!40000 ALTER TABLE `lime_tokens_186734` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_tutorial_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_tutorial_entries` (
  `teid` int(11) NOT NULL AUTO_INCREMENT,
  `ordering` int(11) DEFAULT NULL,
  `title` text DEFAULT NULL,
  `content` mediumtext DEFAULT NULL,
  `settings` mediumtext DEFAULT NULL,
  PRIMARY KEY (`teid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_tutorial_entries` WRITE;
/*!40000 ALTER TABLE `lime_tutorial_entries` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_tutorial_entries` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_tutorial_entry_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_tutorial_entry_relation` (
  `teid` int(11) NOT NULL,
  `tid` int(11) NOT NULL,
  `uid` int(11) DEFAULT NULL,
  `sid` int(11) DEFAULT NULL,
  PRIMARY KEY (`teid`,`tid`),
  KEY `lime_idx1_tutorial_entry_relation` (`uid`),
  KEY `lime_idx2_tutorial_entry_relation` (`sid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_tutorial_entry_relation` WRITE;
/*!40000 ALTER TABLE `lime_tutorial_entry_relation` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_tutorial_entry_relation` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_tutorials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_tutorials` (
  `tid` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) DEFAULT NULL,
  `title` varchar(192) DEFAULT NULL,
  `icon` varchar(64) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `active` int(11) DEFAULT 0,
  `settings` mediumtext DEFAULT NULL,
  `permission` varchar(128) NOT NULL,
  `permission_grade` varchar(128) NOT NULL,
  PRIMARY KEY (`tid`),
  UNIQUE KEY `lime_idx1_tutorials` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_tutorials` WRITE;
/*!40000 ALTER TABLE `lime_tutorials` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_tutorials` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_user_groups` (
  `ugid` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `description` text NOT NULL,
  `owner_id` int(11) NOT NULL,
  PRIMARY KEY (`ugid`),
  UNIQUE KEY `lime_idx1_user_groups` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_user_groups` WRITE;
/*!40000 ALTER TABLE `lime_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_user_groups` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_user_in_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_user_in_groups` (
  `ugid` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  PRIMARY KEY (`ugid`,`uid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_user_in_groups` WRITE;
/*!40000 ALTER TABLE `lime_user_in_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_user_in_groups` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_user_in_permissionrole`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_user_in_permissionrole` (
  `ptid` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  PRIMARY KEY (`ptid`,`uid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_user_in_permissionrole` WRITE;
/*!40000 ALTER TABLE `lime_user_in_permissionrole` DISABLE KEYS */;
/*!40000 ALTER TABLE `lime_user_in_permissionrole` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
DROP TABLE IF EXISTS `lime_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lime_users` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `users_name` varchar(64) NOT NULL DEFAULT '',
  `password` text NOT NULL,
  `full_name` varchar(50) NOT NULL,
  `parent_id` int(11) NOT NULL,
  `lang` varchar(20) DEFAULT NULL,
  `email` varchar(192) DEFAULT NULL,
  `htmleditormode` varchar(7) DEFAULT 'default',
  `templateeditormode` varchar(7) NOT NULL DEFAULT 'default',
  `questionselectormode` varchar(7) NOT NULL DEFAULT 'default',
  `one_time_pw` text DEFAULT NULL,
  `dateformat` int(11) NOT NULL DEFAULT 1,
  `last_login` datetime DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `modified` datetime DEFAULT NULL,
  `validation_key` varchar(38) DEFAULT NULL,
  `validation_key_expiration` datetime DEFAULT NULL,
  `last_forgot_email_password` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `user_status` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`uid`),
  UNIQUE KEY `lime_idx1_users` (`users_name`),
  KEY `lime_idx2_users` (`email`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `lime_users` WRITE;
/*!40000 ALTER TABLE `lime_users` DISABLE KEYS */;
INSERT INTO `lime_users` VALUES
(1,'admin','$2y$10$7DqloEmXXTYt8YkTxw.BsuaZXuU9KZrPUhM31Uv8pQQk7cNwmAJYW','Site Admin',0,'auto','admin@example.org','default','default','default',NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1),
(2,'batchuser','x','Batch User',1,'auto','batchuser@example.org','default','default','default',NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1);
/*!40000 ALTER TABLE `lime_users` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

