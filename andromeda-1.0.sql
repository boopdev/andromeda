
--- Smart Cooldowns
--- This is an important database and cannot be removed. Don't remove it
CREATE TABLE IF NOT EXISTS smartcd(userid BIGINT, guildid BIGINT, channelid BIGINT, cmd TEXT, cd TIMESTAMP);

-- Cookies
CREATE TABLE IF NOT EXISTS cookies(userid BIGINT, given INT, recieved INT);

-- Claiming because FUCK WORSTBOT NIGGA
CREATE TABLE IF NOT EXISTS claims(claimer BIGINT, claimed BIGINT, time TIMESTAMP);

-- Warnings
CREATE TABLE IF NOT EXISTS warnings(warnid SERIAL PRIMARY KEY, userid BIGINT, modid BIGINT, reason TEXT, warned TIMESTAMP);

-- Economy
CREATE TABLE IF NOT EXISTS eco(userid BIGINT, cash INT, bank INT, robbable BOOLEAN DEFAULT FALSE);

-- COCK
CREATE TABLE IF NOT EXISTS penises(userid BIGINT, length REAL, prestige INT, sfwon INT, sflost INT);

--- Mining
CREATE TABLE IF NOT EXISTS mining(
    userid BIGINT, 
    pickaxe TEXT, 
    experience INT, 
    levelnotif INT, 
    oresmined INT
);
CREATE TABLE IF NOT EXISTS ore_definitions(
    oreid SERIAL PRIMARY KEY,
    name TEXT,
    value INT,
    rarity INT
);
CREATE TABLE IF NOT EXISTS ores(
    userid BIGINT,
    oreid SERIAL,
    amount INT
);

-- Fishing Tables
CREATE TABLE IF NOT EXISTS fishing(userid BIGINT, fishing_rod TEXT, experience INT, levelnotif INT, fishcaught INT);
CREATE TABLE IF NOT EXISTS fishing_fishes(fishid TEXT UNIQUE, name TEXT, level INTEGER, minsize REAL, maxsize REAL, price INTEGER);
CREATE TABLE IF NOT EXISTS fishing_leaderboard(userid BIGINT, fishid TEXT UNIQUE, size REAL, caught_at TIMESTAMP);

