-- ============================================================
-- EDE v3 - Schema MCD exact + Vues
-- SSMS : Fichier > Ouvrir > ce fichier, puis F5
-- ============================================================
USE master;
GO
IF EXISTS (SELECT name FROM sys.databases WHERE name='EtudiantDB')
    DROP DATABASE EtudiantDB;
CREATE DATABASE EtudiantDB;
GO
USE EtudiantDB;
GO

-- ============================================================
-- TABLES
-- ============================================================
CREATE TABLE UTILISATEUR (
    id_utilisateur    INT          NOT NULL IDENTITY PRIMARY KEY,
    email_utilisateur VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe      VARCHAR(255) NOT NULL,
    role_utilisateur  VARCHAR(20)  NOT NULL
        CHECK(role_utilisateur IN ('etudiant','professeur','admin')),
    actif             BIT          NOT NULL DEFAULT 1
);
GO

CREATE TABLE MATIERES (
    id_matiere          INT          NOT NULL IDENTITY PRIMARY KEY,
    nom_matiere         VARCHAR(100) NOT NULL,
    coefficient_matiere DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    volume_horaire      VARCHAR(10)  NULL
);
GO

CREATE TABLE Classe (
    id_classe      INT         NOT NULL IDENTITY PRIMARY KEY,
    libelle_classe VARCHAR(30) NOT NULL,
    annee_scolaire VARCHAR(20) NULL
);
GO

CREATE TABLE PROFESSEUR (
    id_prof                    INT          NOT NULL IDENTITY PRIMARY KEY,
    UTILISATEUR_id_utilisateur INT          NOT NULL,
    nom_prof                   VARCHAR(100) NOT NULL,
    prenom_prof                VARCHAR(100) NOT NULL,
    telephone_prof             VARCHAR(20)  NULL,
    FOREIGN KEY (UTILISATEUR_id_utilisateur)
        REFERENCES UTILISATEUR(id_utilisateur)
);
CREATE INDEX PROFESSEUR_FKIndex1 ON PROFESSEUR (UTILISATEUR_id_utilisateur);
CREATE INDEX IFK_Rel_18         ON PROFESSEUR (UTILISATEUR_id_utilisateur);
GO

CREATE TABLE ADMINISTRATEUR (
    id_admin                   INT         NOT NULL IDENTITY PRIMARY KEY,
    UTILISATEUR_id_utilisateur INT         NOT NULL,
    nom                        VARCHAR(50) NULL,
    prenom                     VARCHAR(50) NULL,
    telephone_admin            VARCHAR(15) NULL,
    FOREIGN KEY (UTILISATEUR_id_utilisateur)
        REFERENCES UTILISATEUR(id_utilisateur)
);
CREATE INDEX ADMINISTRATEUR_FKIndex1 ON ADMINISTRATEUR (UTILISATEUR_id_utilisateur);
CREATE INDEX IFK_Rel_19          ON ADMINISTRATEUR (UTILISATEUR_id_utilisateur);
GO

CREATE TABLE ETUDIANT (
    matricule                  INT          NOT NULL IDENTITY PRIMARY KEY,
    Classe_id_classe           INT          NOT NULL,
    UTILISATEUR_id_utilisateur INT          NOT NULL,
    nom                        VARCHAR(100) NOT NULL,
    prenom                     VARCHAR(100) NOT NULL,
    telephone_etudiant         VARCHAR(15)  NULL,
    FOREIGN KEY (Classe_id_classe)
        REFERENCES Classe(id_classe),
    FOREIGN KEY (UTILISATEUR_id_utilisateur)
        REFERENCES UTILISATEUR(id_utilisateur)
);
CREATE INDEX ETUDIANT_FKIndex1 ON ETUDIANT (UTILISATEUR_id_utilisateur);
CREATE INDEX ETUDIANT_FKIndex2 ON ETUDIANT (Classe_id_classe);
CREATE INDEX IFK_Rel_20        ON ETUDIANT (UTILISATEUR_id_utilisateur);
CREATE INDEX IFK_Rel_29        ON ETUDIANT (Classe_id_classe);
GO

CREATE TABLE INTERVIENT (
    PROFESSEUR_id_prof  INT NOT NULL,
    MATIERES_id_matiere INT NOT NULL,
    Classe_id_classe    INT NOT NULL,
    PRIMARY KEY (PROFESSEUR_id_prof, MATIERES_id_matiere, Classe_id_classe),
    FOREIGN KEY (PROFESSEUR_id_prof)  REFERENCES PROFESSEUR(id_prof),
    FOREIGN KEY (MATIERES_id_matiere) REFERENCES MATIERES(id_matiere),
    FOREIGN KEY (Classe_id_classe)    REFERENCES Classe(id_classe)
);
CREATE INDEX INTERVIENT_FKIndex1 ON INTERVIENT (PROFESSEUR_id_prof);
CREATE INDEX INTERVIENT_FKIndex2 ON INTERVIENT (MATIERES_id_matiere);
CREATE INDEX INTERVIENT_FKIndex3 ON INTERVIENT (Classe_id_classe);
CREATE INDEX IFK_Rel_25 ON INTERVIENT (PROFESSEUR_id_prof);
CREATE INDEX IFK_Rel_35 ON INTERVIENT (MATIERES_id_matiere);
CREATE INDEX IFK_Rel_24 ON INTERVIENT (Classe_id_classe);
GO

CREATE TABLE NOTES (
    id_notes            INT          NOT NULL IDENTITY,
    MATIERES_id_matiere INT          NOT NULL,
    PROFESSEUR_id_prof  INT          NOT NULL,
    ETUDIANT_matricule  INT          NOT NULL,
    valeur_note         DECIMAL(5,2) NOT NULL
        CHECK(valeur_note >= 0 AND valeur_note <= 20),
    date_saisie         VARCHAR(20)  NULL,
    PRIMARY KEY (id_notes, MATIERES_id_matiere, PROFESSEUR_id_prof, ETUDIANT_matricule),
    CONSTRAINT UQ_Note_Etudiant_Matiere
        UNIQUE (ETUDIANT_matricule, MATIERES_id_matiere),
    FOREIGN KEY (MATIERES_id_matiere) REFERENCES MATIERES(id_matiere),
    FOREIGN KEY (PROFESSEUR_id_prof)  REFERENCES PROFESSEUR(id_prof),
    FOREIGN KEY (ETUDIANT_matricule)  REFERENCES ETUDIANT(matricule)
);
CREATE INDEX NOTES_FKIndex1 ON NOTES (MATIERES_id_matiere);
CREATE INDEX NOTES_FKIndex2 ON NOTES (PROFESSEUR_id_prof);
CREATE INDEX NOTES_FKIndex3 ON NOTES (ETUDIANT_matricule);
CREATE INDEX IFK_Rel_28  ON NOTES (MATIERES_id_matiere);
CREATE INDEX IFK_Rel_29b ON NOTES (PROFESSEUR_id_prof);
CREATE INDEX IFK_Rel_25b ON NOTES (ETUDIANT_matricule);
GO

CREATE TABLE RESULTAT (
    id_resultat        INT          NOT NULL IDENTITY,
    Classe_id_classe   INT          NOT NULL,
    ETUDIANT_matricule INT          NOT NULL,
    moyenne_generale   DECIMAL(5,2) NULL,
    decision           VARCHAR(20)  NULL
        CHECK(decision IN ('Admis','Ajourne')),
    annee_scolaire     VARCHAR(20)  NULL,
    rang               INT          NULL,
    PRIMARY KEY (id_resultat, Classe_id_classe, ETUDIANT_matricule),
    FOREIGN KEY (Classe_id_classe)   REFERENCES Classe(id_classe),
    FOREIGN KEY (ETUDIANT_matricule) REFERENCES ETUDIANT(matricule)
);
CREATE INDEX RESULTAT_FKIndex1 ON RESULTAT (Classe_id_classe);
CREATE INDEX RESULTAT_FKIndex2 ON RESULTAT (ETUDIANT_matricule);
CREATE INDEX IFK_Rel_33 ON RESULTAT (Classe_id_classe);
CREATE INDEX IFK_Rel_26 ON RESULTAT (ETUDIANT_matricule);
GO

-- ============================================================
-- VUES
-- ============================================================

-- VUE 1 : Notes completes
CREATE OR ALTER VIEW VUE_NOTES_COMPLETES AS
SELECT
    n.id_notes, n.valeur_note, n.date_saisie,
    e.matricule,
    e.nom    AS nom_etudiant,
    e.prenom AS prenom_etudiant,
    e.telephone_etudiant,
    c.id_classe, c.libelle_classe, c.annee_scolaire,
    m.id_matiere, m.nom_matiere, m.coefficient_matiere, m.volume_horaire,
    p.id_prof, p.nom_prof, p.prenom_prof
FROM NOTES n
JOIN ETUDIANT   e ON n.ETUDIANT_matricule  = e.matricule
JOIN MATIERES   m ON n.MATIERES_id_matiere = m.id_matiere
JOIN PROFESSEUR p ON n.PROFESSEUR_id_prof  = p.id_prof
JOIN Classe     c ON e.Classe_id_classe    = c.id_classe;
GO

-- VUE 2 : Moyennes ponderees par etudiant
CREATE OR ALTER VIEW VUE_MOYENNES_ETUDIANTS AS
SELECT
    e.matricule, e.nom, e.prenom, e.telephone_etudiant,
    c.id_classe, c.libelle_classe, c.annee_scolaire,
    COUNT(n.id_notes) AS nb_matieres,
    CAST(
        SUM(n.valeur_note * m.coefficient_matiere)
        / NULLIF(SUM(m.coefficient_matiere), 0)
    AS DECIMAL(5,2)) AS moyenne_generale,
    CASE
        WHEN SUM(n.valeur_note * m.coefficient_matiere)
             / NULLIF(SUM(m.coefficient_matiere), 0) >= 12
        THEN 'Admis' ELSE 'Ajourne'
    END AS decision
FROM ETUDIANT  e
JOIN Classe    c ON e.Classe_id_classe    = c.id_classe
LEFT JOIN NOTES    n ON n.ETUDIANT_matricule  = e.matricule
LEFT JOIN MATIERES m ON n.MATIERES_id_matiere = m.id_matiere
GROUP BY e.matricule, e.nom, e.prenom, e.telephone_etudiant,
         c.id_classe, c.libelle_classe, c.annee_scolaire;
GO

-- VUE 3 : Classement par classe
CREATE OR ALTER VIEW VUE_CLASSEMENT_CLASSE AS
SELECT *,
    RANK() OVER (PARTITION BY id_classe
                 ORDER BY ISNULL(moyenne_generale, 0) DESC) AS rang
FROM VUE_MOYENNES_ETUDIANTS;
GO

-- VUE 4 : Statistiques par classe
CREATE OR ALTER VIEW VUE_STATS_CLASSE AS
SELECT
    c.id_classe, c.libelle_classe, c.annee_scolaire,
    COUNT(DISTINCT e.matricule)                                             AS nb_etudiants,
    CAST(AVG(mv.moyenne_generale)  AS DECIMAL(5,2))                        AS moyenne_classe,
    CAST(MAX(mv.moyenne_generale)  AS DECIMAL(5,2))                        AS note_max,
    CAST(MIN(mv.moyenne_generale)  AS DECIMAL(5,2))                        AS note_min,
    SUM(CASE WHEN mv.decision='Admis'   THEN 1 ELSE 0 END)                 AS nb_admis,
    SUM(CASE WHEN mv.decision='Ajourne' THEN 1 ELSE 0 END)                 AS nb_ajournes,
    CAST(
        SUM(CASE WHEN mv.decision='Admis' THEN 1.0 ELSE 0 END)
        / NULLIF(COUNT(DISTINCT e.matricule), 0) * 100
    AS DECIMAL(5,1))                                                        AS taux_reussite
FROM Classe c
LEFT JOIN ETUDIANT               e  ON e.Classe_id_classe = c.id_classe
LEFT JOIN VUE_MOYENNES_ETUDIANTS mv ON mv.matricule       = e.matricule
GROUP BY c.id_classe, c.libelle_classe, c.annee_scolaire;
GO

-- VUE 5 : Enseignements (prof + matiere + classe)
CREATE OR ALTER VIEW VUE_ENSEIGNEMENTS AS
SELECT
    p.id_prof, p.nom_prof, p.prenom_prof, p.telephone_prof,
    m.id_matiere, m.nom_matiere, m.coefficient_matiere, m.volume_horaire,
    c.id_classe, c.libelle_classe, c.annee_scolaire
FROM INTERVIENT i
JOIN PROFESSEUR p ON i.PROFESSEUR_id_prof  = p.id_prof
JOIN MATIERES   m ON i.MATIERES_id_matiere = m.id_matiere
JOIN Classe     c ON i.Classe_id_classe    = c.id_classe;
GO

-- VUE 6 : Resultats officiels
CREATE OR ALTER VIEW VUE_RESULTATS_COMPLETS AS
SELECT
    r.id_resultat, r.annee_scolaire, r.rang,
    r.moyenne_generale, r.decision,
    e.matricule,
    e.nom    AS nom_etudiant,
    e.prenom AS prenom_etudiant,
    c.id_classe, c.libelle_classe
FROM RESULTAT r
JOIN ETUDIANT e ON r.ETUDIANT_matricule = e.matricule
JOIN Classe   c ON r.Classe_id_classe   = c.id_classe;
GO

-- VUE 7 : Statistiques globales
CREATE OR ALTER VIEW VUE_STATS_GLOBALES AS
SELECT
    (SELECT COUNT(*) FROM ETUDIANT)   AS nb_etudiants,
    (SELECT COUNT(*) FROM PROFESSEUR) AS nb_professeurs,
    (SELECT COUNT(*) FROM Classe)     AS nb_classes,
    (SELECT COUNT(*) FROM MATIERES)   AS nb_matieres,
    (SELECT COUNT(*) FROM NOTES)      AS nb_notes,
    (SELECT CAST(AVG(CAST(valeur_note AS FLOAT)) AS DECIMAL(5,2)) FROM NOTES)
                                      AS moyenne_globale;
GO

-- ============================================================
-- DONNEES 
-- ============================================================


-- UTILISATEURS
INSERT INTO UTILISATEUR (email_utilisateur, mot_de_passe, role_utilisateur) VALUES
('barry.thierno@ede.sn','TEMP','admin'),

('thiaw@ede.sn','TEMP','professeur'),
('ndiaye.moussa@ede.sn','TEMP','professeur'),
('ba.aissatou@ede.sn','TEMP','professeur'),
('sarr.abdou@ede.sn','TEMP','professeur'),

('ousmane.ndiaye@ede.sn','TEMP','etudiant'),
('fatou.diop@ede.sn','TEMP','etudiant'),
('mamadou.fall@ede.sn','TEMP','etudiant'),
('awa.sarr@ede.sn','TEMP','etudiant'),
('cheikh.kane@ede.sn','TEMP','etudiant'),
('ibrahima.sy@ede.sn','TEMP','etudiant');
GO

-- ADMINISTRATEUR
INSERT INTO ADMINISTRATEUR (UTILISATEUR_id_utilisateur,nom,prenom,telephone_admin)
VALUES
(1,'Barry','Thierno Ibrahima','+221770000000');
GO

-- PROFESSEURS
INSERT INTO PROFESSEUR (UTILISATEUR_id_utilisateur,nom_prof,prenom_prof,telephone_prof) VALUES
(2,'Thiaw','Mamadou','+221771111111'),
(3,'Ndiaye','Moussa','+221772222222'),
(4,'Ba','Aissatou','+221773333333'),
(5,'Sarr','Abdou','+221774444444');
GO

-- CLASSES (ISE)
INSERT INTO Classe (libelle_classe,annee_scolaire) VALUES
('ISE1','2025-2026'),
('ISE2','2025-2026'),
('ISE3','2025-2026');
GO

-- MATIERES (programme plausible ISE)
INSERT INTO MATIERES (nom_matiere,coefficient_matiere,volume_horaire) VALUES
('Algorithmique',3,'45h'),
('Bases de Donnees',3,'45h'),
('Analyse Mathematique',4,'60h'),
('Algebre Lineaire',3,'45h'),
('Developpement Web',2,'30h'),
('Theorie des Tests',3,'45h'),
('Econometrie',4,'60h'),
('Statistiques Descriptives',3,'45h'),
('Probabilites',3,'45h'),
('Machine Learning',3,'45h');
GO

-- ETUDIANTS SENEGALAIS
INSERT INTO ETUDIANT (Classe_id_classe,UTILISATEUR_id_utilisateur,nom,prenom,telephone_etudiant) VALUES
(1,6,'Ndiaye','Ousmane','+221776543210'),
(1,7,'Diop','Fatou','+221777654321'),
(2,8,'Fall','Mamadou','+221778765432'),
(2,9,'Sarr','Awa','+221779876543'),
(3,10,'Kane','Cheikh','+221770112233'),
(3,11,'Sy','Ibrahima','+221771223344');
GO

-- AFFECTATION PROFESSEUR / MATIERE / CLASSE
INSERT INTO INTERVIENT (PROFESSEUR_id_prof,MATIERES_id_matiere,Classe_id_classe) VALUES
(1,1,1),
(1,2,1),
(2,3,1),
(2,4,2),
(3,5,2),
(3,6,3),
(4,7,3),
(4,8,1),
(2,9,2),
(1,10,3);
GO

-- NOTES DES ETUDIANTS
INSERT INTO NOTES (MATIERES_id_matiere,PROFESSEUR_id_prof,ETUDIANT_matricule,valeur_note,date_saisie) VALUES

(1,1,1,15.5,'2025-03-01'),
(2,1,1,14,'2025-03-02'),
(3,2,1,13.5,'2025-03-03'),

(1,1,2,12,'2025-03-01'),
(2,1,2,13,'2025-03-02'),
(3,2,2,11,'2025-03-03'),

(4,2,3,14,'2025-03-01'),
(5,3,3,15,'2025-03-02'),

(4,2,4,10,'2025-03-01'),
(5,3,4,11,'2025-03-02'),

(7,4,5,16,'2025-03-01'),
(6,3,5,15,'2025-03-02'),

(7,4,6,13,'2025-03-01'),
(10,1,6,14,'2025-03-02');
GO

PRINT 'Base EtudiantDB creee avec succes!';
PRINT 'Donnees adaptees au programme ISE';
PRINT 'Etape suivante : python setup_passwords.py';
GO