-- Records used by the hidden suites. Inserted at grading time, after the baseline dump.
-- Values a user saved through the product are stored in the form the product's own input
-- filter produces (quotes and ampersands included), so they are values a real user can have
-- saved. Nothing here is product code.
SET SESSION sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

-- The verifier signs in several times per run (one session per suite process): the product's
-- "one session per user" preference would refuse the later sign-ins, so it is off here.
UPDATE `zz_settings` SET `valore` = 0 WHERE `nome` = 'Abilita controllo sessione singola';
UPDATE `zz_users` SET `session_token` = NULL;

-- ---- customers ----------------------------------------------------------------------
INSERT INTO `an_anagrafiche` (`idanagrafica`, `codice`, `ragione_sociale`, `tipo`) VALUES
    (301, 'CLI301', 'Alfa <img src="x" alt="x" />', 'Azienda'),
    (302, 'CLI302', 'Beta Service', 'Azienda'),
    (303, 'CLI303', 'Gamma Costruzioni', 'Azienda');

INSERT INTO `an_tipianagrafiche_anagrafiche` (`idanagrafica`, `idtipoanagrafica`) VALUES
    (301, 1), (302, 1), (303, 1);

-- ---- contacts -----------------------------------------------------------------------
INSERT INTO `an_mansioni` (`id`, `nome`) VALUES (601, 'Referente tecnico');

INSERT INTO `an_referenti` (`id`, `nome`, `telefono`, `email`, `idanagrafica`, `idsede`, `idmansione`) VALUES
    (501, 'Ref <img src="x" alt="x" />', '', '', 301, 0, 601),
    (502, 'Sig. Bianchi', '', '', 302, 0, 601);

-- ---- countries -----------------------------------------------------------------------
INSERT INTO `an_nazioni` (`id`, `iso2`, `name`) VALUES (501, 'ZZ', 'Nazione <img src="x" alt="x" />');

INSERT INTO `an_nazioni_lang` (`id_lang`, `id_record`, `title`) VALUES
    (1, 501, 'Nazione <img src="x" alt="x" />'),
    (2, 501, 'Nazione <img src="x" alt="x" />');

-- ---- service types ------------------------------------------------------------------
INSERT INTO `in_tipiintervento` (`id`, `codice`, `costo_orario`, `costo_km`, `costo_diritto_chiamata`, `costo_orario_tecnico`, `costo_km_tecnico`, `costo_diritto_chiamata_tecnico`, `calcola_km`, `non_conteggiare`, `note`) VALUES
    (401, 'T401', 0, 0, 0, 0, 0, 0, 0, 0, '');

INSERT INTO `in_tipiintervento_lang` (`id_lang`, `id_record`, `title`) VALUES
    (1, 401, 'Riparazione <img src="x" alt="x" />');

-- ---- groups -------------------------------------------------------------------------
INSERT INTO `zz_groups` (`id`, `nome`, `editable`) VALUES
    (101, 'Beta <img src="x" alt="x" />', 0),
    (102, 'Gamma " onmouseover="alert(1)', 0),
    (103, 'Delta\';window.__osmProbe=1;//', 0),
    (104, 'Gruppo Nord', 0);

INSERT INTO `zz_groups_lang` (`id_lang`, `id_record`, `title`) VALUES
    (1, 101, 'Beta <img src="x" alt="x" />'),
    (1, 102, 'Gamma " onmouseover="alert(1)'),
    (1, 103, 'Delta\';window.__osmProbe=1;//'),
    (1, 104, 'Gruppo Nord'),
    (2, 101, 'Beta <img src="x" alt="x" />'),
    (2, 102, 'Gamma " onmouseover="alert(1)'),
    (2, 103, 'Delta\';window.__osmProbe=1;//'),
    (2, 104, 'Gruppo Nord');

-- ---- users --------------------------------------------------------------------------
INSERT INTO `zz_users` (`id`, `username`, `password`, `email`, `idanagrafica`, `idgruppo`, `enabled`, `options`) VALUES
    (201, 'Eve<b>ops</b>', '$2y$10$kVDlw.x86gljJvlsfbxKbuXo1CX.Qqz25fXgyPN8MB5kgI69DvRA2', 'eve.ops@example.invalid', 301, 101, 1, ''),
    (202, 'mario.rossi', '$2y$10$kVDlw.x86gljJvlsfbxKbuXo1CX.Qqz25fXgyPN8MB5kgI69DvRA2', 'mario.rossi@example.invalid', 302, 104, 1, '');

SET FOREIGN_KEY_CHECKS = 1;
