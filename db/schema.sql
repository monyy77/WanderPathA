CREATE DATABASE IF NOT EXISTS wanderpath_db;
USE wanderpath_db;

CREATE TABLE Airports (
    airport_code VARCHAR(10) PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    weather VARCHAR(100),
    status VARCHAR(50) NOT NULL
);

CREATE TABLE Flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    estimated_departure_time DATETIME NOT NULL,
    estimated_arrival_time DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL,
    delay_minutes INT,
    disruption_reason VARCHAR(255),
    connection_risk BOOLEAN,
    severity VARCHAR(30),

    FOREIGN KEY (origin_airport)
        REFERENCES Airports(airport_code),

    FOREIGN KEY (destination_airport)
        REFERENCES Airports(airport_code)
);

CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) NOT NULL,
    nationality VARCHAR(100) NOT NULL,
    vip BOOLEAN NOT NULL,
    passport VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE Bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    flight_id INT,
    booking_date DATETIME NOT NULL,
    trip_cost DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    refund_eligible BOOLEAN,
    ticket_type VARCHAR(100),
    refund_amount DECIMAL(10,2),
	compensation DECIMAL(10,2),
    FOREIGN KEY (customer_id)
        REFERENCES Customers(customer_id),

    FOREIGN KEY (flight_id)
        REFERENCES Flights(flight_id)
);

CREATE TABLE AlternativeTransport (

    transport_id INT AUTO_INCREMENT PRIMARY KEY,
    destination_airport VARCHAR(10),
    transport_type VARCHAR(100),
    provider VARCHAR(100),
    departure_time DATETIME,
    arrival_time DATETIME,
    price DECIMAL(10,2),
    FOREIGN KEY (destination_airport)
        REFERENCES Airports(airport_code)
);

CREATE TABLE Employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Refunds (
    refund_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    processed_by INT,
    refund_amount DECIMAL(10,2),
    status VARCHAR(50) NOT NULL,
    processed_date DATETIME NOT NULL,
    FOREIGN KEY (booking_id)
        REFERENCES Bookings(booking_id),

    FOREIGN KEY (processed_by)
        REFERENCES Employees(employee_id)
);

CREATE TABLE Escalations (
    escalation_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    customer_id INT,
    employee_id INT,
    reason VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_date DATETIME NOT NULL,
    FOREIGN KEY (booking_id)
        REFERENCES Bookings(booking_id),
    FOREIGN KEY (customer_id)
        REFERENCES Customers(customer_id),
    FOREIGN KEY (employee_id)
        REFERENCES Employees(employee_id)
);

-- ============================================================
-- Added for Final Project: State Graph checkpointing (Issue #1)
-- Owner: Person 1
-- Append-only log: every meaningful transition inserts a NEW row,
-- never UPDATEs an old one. This gives us full history for the
-- crash-and-resume demo, and for showing HITL/failure state later.
-- ============================================================
CREATE TABLE GraphCheckpoints (
    checkpoint_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,
    graph_name VARCHAR(100) NOT NULL,
    current_node VARCHAR(100) NOT NULL,
    state_json JSON NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    INDEX idx_run_id_created (run_id, created_at)
);

-- ============================================================
-- Added for Final Project: MCP tool registry data boundary (Issue #4)
-- Owner: Person 1
--
-- WHY THIS TABLE EXISTS:
-- Prior grading flagged that the MCP Server Lab had no attributable
-- domain-data ownership - protocol/integration code existed, but no
-- documented schema or data-boundary work. This table is that
-- boundary: it defines exactly what a "registered tool" record is,
-- so tool registration/deregistration (Issue #5, driven from the
-- admin panel) has a real, validated data store behind it instead of
-- being an in-memory-only toggle that disappears on restart.
-- ============================================================
CREATE TABLE RegisteredTools (
    tool_id INT AUTO_INCREMENT PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL UNIQUE,
    agent_name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    parameters_schema JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_is_active (is_active)
);

CREATE TABLE IF NOT EXISTS FailureTickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL,
    failed_node VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    status ENUM('open', 'investigating', 'resolved') DEFAULT 'open',
    resolution_notes TEXT NULL,
    checkpoint_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (checkpoint_id) REFERENCES GraphCheckpoints(checkpoint_id)
);

-- Seed data: register the tools that already exist in tools/ so the
-- registry reflects reality from day one, rather than starting empty
-- and pretending no tools exist until someone registers them by hand.
INSERT INTO RegisteredTools (tool_name, agent_name, description, parameters_schema, is_active) VALUES
('search_flights', 'flight_rebooking', 'Search for alternative flights given an origin/destination/date range.', JSON_OBJECT('flight_id', 'int', 'date_range', 'string'), TRUE),
('cancel_booking', 'flight_rebooking', 'Cancel an existing booking by booking_id.', JSON_OBJECT('booking_id', 'int'), TRUE),
('process_refund', 'flight_rebooking', 'Process a refund for a booking, given an approved amount.', JSON_OBJECT('booking_id', 'int', 'amount', 'float'), TRUE);