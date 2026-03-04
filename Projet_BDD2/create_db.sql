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
             / NULLIF(SUM(m.coefficient_matiere), 0) >= 10
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
-- DONNEES DE TEST
-- ============================================================
INSERT INTO UTILISATEUR (email_utilisateur, mot_de_passe, role_utilisateur) VALUES
('admin@ede.ca',   'TEMP', 'admin'),
('dupont@ede.ca',  'TEMP', 'professeur'),
('martin@ede.ca',  'TEMP', 'professeur'),
('leblanc@ede.ca', 'TEMP', 'professeur'),
('alice@ede.ca',   'TEMP', 'etudiant'),
('marc@ede.ca',    'TEMP', 'etudiant'),
('sophie@ede.ca',  'TEMP', 'etudiant'),
('karim@ede.ca',   'TEMP', 'etudiant');
GO
INSERT INTO ADMINISTRATEUR (UTILISATEUR_id_utilisateur,nom,prenom,telephone_admin)
VALUES (1,'Admin','Principal','0600000000');
GO
INSERT INTO PROFESSEUR (UTILISATEUR_id_utilisateur,nom_prof,prenom_prof,telephone_prof) VALUES
(2,'Dupont','Jean','0611111111'),
(3,'Martin','Marie','0622222222'),
(4,'Leblanc','Pierre','0633333333');
GO
INSERT INTO Classe (libelle_classe,annee_scolaire) VALUES
('INF-L1','2024-2025'),('INF-L2','2024-2025'),('RT-L1','2024-2025');
GO
INSERT INTO MATIERES (nom_matiere,coefficient_matiere,volume_horaire) VALUES
('Algorithmique',3.00,'45h'),('Bases de Donnees',3.00,'45h'),
('Reseaux',2.00,'30h'),('Mathematiques',4.00,'60h'),
('Developpement Web',2.00,'30h'),('Programmation Python',3.00,'45h');
GO
INSERT INTO ETUDIANT (Classe_id_classe,UTILISATEUR_id_utilisateur,nom,prenom,telephone_etudiant) VALUES
(1,5,'Tremblay','Alice','0644444444'),
(1,6,'Bouchard','Marc','0655555555'),
(2,7,'Gagnon','Sophie','0666666666'),
(3,8,'Diallo','Karim','0677777777');
GO
INSERT INTO INTERVIENT (PROFESSEUR_id_prof,MATIERES_id_matiere,Classe_id_classe) VALUES
(1,1,1),(1,2,1),(1,5,1),(2,4,1),(2,4,2),(3,3,3),(1,6,2);
GO
INSERT INTO NOTES (MATIERES_id_matiere,PROFESSEUR_id_prof,ETUDIANT_matricule,valeur_note,date_saisie) VALUES
(1,1,1,14.50,'2024-11-01'),(2,1,1,16.00,'2024-11-02'),
(4,2,1,13.00,'2024-11-03'),(5,1,1,15.50,'2024-11-04'),
(1,1,2,9.00,'2024-11-01'),(2,1,2,11.50,'2024-11-02'),(4,2,2,8.00,'2024-11-03'),
(4,2,3,17.00,'2024-11-01'),(6,1,3,14.00,'2024-11-02'),
(3,3,4,12.50,'2024-11-01');
GO

PRINT 'Base EtudiantDB creee avec succes!';
PRINT 'Etape suivante : python setup_passwords.py';
GO
