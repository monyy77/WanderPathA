USE wanderpath_db;


INSERT INTO Airports
(airport_code, airport_name, city, country, weather, status)
VALUES
('CAI', 'Cairo International Airport', 'Cairo', 'Egypt', 'Sunny', 'Operational'),
('DXB', 'Dubai International Airport', 'Dubai', 'UAE', 'Clear', 'Operational'),
('JED', 'King Abdulaziz International Airport', 'Jeddah', 'Saudi Arabia', 'Cloudy', 'Operational'),
('LHR', 'London Heathrow Airport', 'London', 'United Kingdom', 'Rainy', 'Operational');


INSERT INTO Flights
(origin_airport, destination_airport, departure_time, arrival_time,
estimated_departure_time, estimated_arrival_time,
status, delay_minutes, disruption_reason, connection_risk)
VALUES
('CAI', 'DXB',
'2026-08-01 08:00:00',
'2026-08-01 12:00:00',
'2026-08-01 08:00:00',
'2026-08-01 12:00:00',
'On Time',
0,
NULL,
FALSE),

('CAI', 'JED',
'2026-08-02 09:00:00',
'2026-08-02 11:00:00',
'2026-08-02 11:00:00',
'2026-08-02 13:00:00',
'Delayed',
120,
'Bad Weather',
TRUE),

('DXB', 'LHR',
'2026-08-03 14:00:00',
'2026-08-03 20:00:00',
'2026-08-03 18:00:00',
'2026-08-04 00:00:00',
'Cancelled',
0,
'Technical Issue',
FALSE);


INSERT INTO Customers
(first_name, last_name, email, phone, nationality, vip, passport)
VALUES
('Ahmed', 'Ali', 'ahmed@example.com', '+201001112223', 'Egyptian', FALSE, 'A1234567'),
('Sara', 'Mohamed', 'sara@example.com', '+201005554443', 'Egyptian', TRUE, 'B9876543'),
('Omar', 'Hassan', 'omar@example.com', '+201009998887', 'Saudi', FALSE, 'C5678901');


INSERT INTO Bookings
(customer_id, flight_id, booking_date,
trip_cost, status, refund_eligible, ticket_type)
VALUES
(1, 1,
'2026-07-20 10:00:00',
350.00,
'Confirmed',
FALSE,
'Economy'),

(2, 2,
'2026-07-22 12:00:00',
500.00,
'Delayed',
TRUE,
'Business'),

(3, 3,
'2026-07-23 15:00:00',
700.00,
'Cancelled',
TRUE,
'First');


INSERT INTO Employees
(name, role, email)
VALUES
('Mona Adel', 'Support', 'mona@travel.com'),
('Karim Hassan', 'Supervisor', 'karim@travel.com'),
('Nour Ali', 'Manager', 'nour@travel.com');


INSERT INTO Refunds
(booking_id, processed_by,
refund_amount, status, processed_date)
VALUES
(
3,
3,
700.00,
'Processed',
'2026-07-24 10:30:00'
);

INSERT INTO AlternativeTransport
(destination_airport, transport_type, provider,
departure_time, arrival_time, price)
VALUES
('DXB','Bus','Emirates Bus',
'2026-08-01 13:00:00',
'2026-08-01 18:00:00',
80),

('LHR','Train','National Rail',
'2026-08-03 21:00:00',
'2026-08-03 23:00:00',
60);

INSERT INTO Escalations
(booking_id, employee_id,
reason, status, created_date)
VALUES
(
2,
2,
'Customer requested urgent rebooking after long delay',
'Open',
'2026-07-22 13:15:00'
);
