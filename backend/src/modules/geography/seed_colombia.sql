-- =============================================================================
-- Geography Seed: Colombia (Complete) + Latin American Countries
-- =============================================================================
-- Idempotent: safe to run multiple times.
-- Uses ON CONFLICT DO NOTHING and conditional inserts.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Create tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS geo_countries (
    id INTEGER PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone_code VARCHAR(10),
    currency VARCHAR(5),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS geo_states (
    id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES geo_countries(id),
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    UNIQUE(country_id, code)
);

CREATE TABLE IF NOT EXISTS geo_cities (
    id SERIAL PRIMARY KEY,
    state_id INTEGER NOT NULL REFERENCES geo_states(id),
    code VARCHAR(20),
    name VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_geo_states_country ON geo_states(country_id);
CREATE INDEX IF NOT EXISTS idx_geo_cities_state ON geo_cities(state_id);
CREATE INDEX IF NOT EXISTS idx_geo_cities_name ON geo_cities(name);

-- ---------------------------------------------------------------------------
-- 2. Insert countries
-- ---------------------------------------------------------------------------

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (170, 'CO', 'Colombia', '+57', 'COP')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (862, 'VE', 'Venezuela', '+58', 'VES')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (218, 'EC', 'Ecuador', '+593', 'USD')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (604, 'PE', 'Perú', '+51', 'PEN')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (484, 'MX', 'México', '+52', 'MXN')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (840, 'US', 'Estados Unidos', '+1', 'USD')
ON CONFLICT (code) DO NOTHING;

INSERT INTO geo_countries (id, code, name, phone_code, currency) VALUES
    (591, 'PA', 'Panamá', '+507', 'PAB')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 3. Insert Colombian departments (33 total: 32 departments + Bogotá D.C.)
-- ---------------------------------------------------------------------------

INSERT INTO geo_states (country_id, code, name) VALUES (170, '05', 'Antioquia') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '08', 'Atlántico') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '11', 'Bogotá D.C.') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '13', 'Bolívar') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '15', 'Boyacá') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '17', 'Caldas') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '18', 'Caquetá') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '19', 'Cauca') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '20', 'Cesar') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '23', 'Córdoba') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '25', 'Cundinamarca') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '27', 'Chocó') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '41', 'Huila') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '44', 'La Guajira') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '47', 'Magdalena') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '50', 'Meta') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '52', 'Nariño') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '54', 'Norte de Santander') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '63', 'Quindío') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '66', 'Risaralda') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '68', 'Santander') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '70', 'Sucre') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '73', 'Tolima') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '76', 'Valle del Cauca') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '81', 'Arauca') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '85', 'Casanare') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '86', 'Putumayo') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '88', 'San Andrés y Providencia') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '91', 'Amazonas') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '94', 'Guainía') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '95', 'Guaviare') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '97', 'Vaupés') ON CONFLICT (country_id, code) DO NOTHING;
INSERT INTO geo_states (country_id, code, name) VALUES (170, '99', 'Vichada') ON CONFLICT (country_id, code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4. Insert cities/municipalities for each department
-- ---------------------------------------------------------------------------
-- Wrapped in a DO block to avoid duplicate inserts on re-run.

DO $$
BEGIN
  IF NOT EXISTS (
      SELECT 1 FROM geo_cities gc
      JOIN geo_states gs ON gc.state_id = gs.id
      WHERE gs.country_id = 170
      LIMIT 1
  ) THEN

    -- -----------------------------------------------------------------------
    -- Antioquia (05)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Medellín'), ('Bello'), ('Itagüí'), ('Envigado'), ('Rionegro'),
        ('Apartadó'), ('Turbo'), ('Caucasia'), ('Marinilla'), ('La Ceja'),
        ('El Carmen de Viboral'), ('Copacabana'), ('Sabaneta'), ('Barbosa'),
        ('Girardota'), ('Caldas')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '05';

    -- -----------------------------------------------------------------------
    -- Atlántico (08)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Barranquilla'), ('Soledad'), ('Malambo'), ('Sabanalarga'),
        ('Galapa'), ('Puerto Colombia'), ('Baranoa')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '08';

    -- -----------------------------------------------------------------------
    -- Bogotá D.C. (11)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Bogotá')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '11';

    -- -----------------------------------------------------------------------
    -- Bolívar (13)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Cartagena'), ('Magangué'), ('Turbaco'), ('Arjona'),
        ('San Juan Nepomuceno'), ('El Carmen de Bolívar')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '13';

    -- -----------------------------------------------------------------------
    -- Boyacá (15)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Tunja'), ('Duitama'), ('Sogamoso'), ('Chiquinquirá'),
        ('Paipa'), ('Villa de Leyva')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '15';

    -- -----------------------------------------------------------------------
    -- Caldas (17)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Manizales'), ('La Dorada'), ('Chinchiná'), ('Villamaría'),
        ('Anserma')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '17';

    -- -----------------------------------------------------------------------
    -- Caquetá (18)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Florencia'), ('San Vicente del Caguán'), ('El Doncello')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '18';

    -- -----------------------------------------------------------------------
    -- Cauca (19)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Popayán'), ('Santander de Quilichao'), ('Puerto Tejada'),
        ('Piendamó')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '19';

    -- -----------------------------------------------------------------------
    -- Cesar (20)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Valledupar'), ('Aguachica'), ('Codazzi'), ('Bosconia'),
        ('La Paz')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '20';

    -- -----------------------------------------------------------------------
    -- Córdoba (23)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Montería'), ('Cereté'), ('Lorica'), ('Sahagún'),
        ('Montelíbano'), ('Tierralta')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '23';

    -- -----------------------------------------------------------------------
    -- Cundinamarca (25)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Soacha'), ('Facatativá'), ('Zipaquirá'), ('Chía'),
        ('Fusagasugá'), ('Girardot'), ('Madrid'), ('Mosquera'),
        ('Funza'), ('Cajicá'), ('La Calera'), ('Cota'), ('Sibaté'),
        ('Tocancipá'), ('Sopó'), ('Tabio'), ('Tenjo'), ('Nemocón')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '25';

    -- -----------------------------------------------------------------------
    -- Chocó (27)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Quibdó'), ('Istmina'), ('Tadó'), ('Condoto')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '27';

    -- -----------------------------------------------------------------------
    -- Huila (41)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Neiva'), ('Pitalito'), ('Garzón'), ('La Plata'),
        ('Campoalegre')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '41';

    -- -----------------------------------------------------------------------
    -- La Guajira (44)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Riohacha'), ('Maicao'), ('Uribia'), ('Manaure')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '44';

    -- -----------------------------------------------------------------------
    -- Magdalena (47)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Santa Marta'), ('Ciénaga'), ('Fundación'), ('El Banco'),
        ('Plato')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '47';

    -- -----------------------------------------------------------------------
    -- Meta (50)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Villavicencio'), ('Acacías'), ('Granada'), ('San Martín'),
        ('Puerto López')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '50';

    -- -----------------------------------------------------------------------
    -- Nariño (52)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Pasto'), ('Tumaco'), ('Ipiales'), ('La Unión'), ('Túquerres')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '52';

    -- -----------------------------------------------------------------------
    -- Norte de Santander (54)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Cúcuta'), ('Ocaña'), ('Pamplona'), ('Villa del Rosario'),
        ('Los Patios')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '54';

    -- -----------------------------------------------------------------------
    -- Quindío (63)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Armenia'), ('Calarcá'), ('La Tebaida'), ('Montenegro'),
        ('Circasia')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '63';

    -- -----------------------------------------------------------------------
    -- Risaralda (66)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Pereira'), ('Dosquebradas'), ('Santa Rosa de Cabal'),
        ('La Virginia')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '66';

    -- -----------------------------------------------------------------------
    -- Santander (68)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Bucaramanga'), ('Floridablanca'), ('Girón'), ('Piedecuesta'),
        ('Barrancabermeja'), ('San Gil')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '68';

    -- -----------------------------------------------------------------------
    -- Sucre (70)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Sincelejo'), ('Corozal'), ('San Marcos'), ('Tolú'),
        ('San Onofre')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '70';

    -- -----------------------------------------------------------------------
    -- Tolima (73)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Ibagué'), ('Espinal'), ('Melgar'), ('Honda'), ('Líbano'),
        ('Mariquita')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '73';

    -- -----------------------------------------------------------------------
    -- Valle del Cauca (76)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Cali'), ('Buenaventura'), ('Palmira'), ('Tuluá'), ('Buga'),
        ('Cartago'), ('Yumbo'), ('Jamundí'), ('Candelaria'), ('Florida')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '76';

    -- -----------------------------------------------------------------------
    -- Arauca (81)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Arauca'), ('Saravena'), ('Tame'), ('Fortul')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '81';

    -- -----------------------------------------------------------------------
    -- Casanare (85)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Yopal'), ('Aguazul'), ('Villanueva'), ('Tauramena')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '85';

    -- -----------------------------------------------------------------------
    -- Putumayo (86)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Mocoa'), ('Puerto Asís'), ('Orito')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '86';

    -- -----------------------------------------------------------------------
    -- San Andrés y Providencia (88)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('San Andrés'), ('Providencia')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '88';

    -- -----------------------------------------------------------------------
    -- Amazonas (91)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Leticia')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '91';

    -- -----------------------------------------------------------------------
    -- Guainía (94)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Inírida')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '94';

    -- -----------------------------------------------------------------------
    -- Guaviare (95)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('San José del Guaviare')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '95';

    -- -----------------------------------------------------------------------
    -- Vaupés (97)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Mitú')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '97';

    -- -----------------------------------------------------------------------
    -- Vichada (99)
    -- -----------------------------------------------------------------------
    INSERT INTO geo_cities (state_id, name)
    SELECT s.id, c.city_name
    FROM geo_states s,
    (VALUES
        ('Puerto Carreño')
    ) AS c(city_name)
    WHERE s.country_id = 170 AND s.code = '99';

  END IF;
END $$;

-- =============================================================================
-- Summary:
--   7 countries inserted (Colombia + 6 Latin American)
--   33 Colombian departments/states inserted
--   ~170 Colombian cities/municipalities inserted
-- =============================================================================
