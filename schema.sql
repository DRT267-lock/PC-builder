CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cpus (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    socket TEXT NOT NULL,
    cores INT,
    tdp INT,
    price INT
);
CREATE TABLE motherboards (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    socket TEXT NOT NULL,
    form_factor TEXT NOT NULL,
    ram_type TEXT NOT NULL,
    max_ram INT,
    price INT
);
CREATE TABLE gpus (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    chipset TEXT,
    vram INT,
    length INT,
    tdp INT,
    price INT
);
CREATE TABLE rams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    size INT,
    speed INT,
    price INT
);
CREATE TABLE storages (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    capacity INT,
    price INT
);
CREATE TABLE psus (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    power INT NOT NULL,
    modular BOOLEAN,
    price INT
);
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    form_factor TEXT NOT NULL,
    gpu_max_length INT,
    psu_form_factor TEXT,
    price INT
);
CREATE TABLE coolers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    socket TEXT NOT NULL,
    tdp_capacity INT,
    price INT
);

CREATE TABLE builds (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    cpu_id INT REFERENCES cpus(id),
    motherboard_id INT REFERENCES motherboards(id),
    gpu_id INT REFERENCES gpus(id),
    ram_id INT REFERENCES rams(id),
    storage_id INT REFERENCES storages(id),
    psu_id INT REFERENCES psus(id),
    case_id INT REFERENCES cases(id),
    cooler_id INT REFERENCES coolers(id),
    total_price INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
