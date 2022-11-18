CREATE TABLE `Projects` (
  id INT(11) NOT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `code` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id)
);
insert into `Projects` (`id`, `name`, `code`) values (1, 'DevOps', 'DO180');
