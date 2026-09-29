-- =============================================================
-- sample_data.sql  (PostgreSQL / Supabase edition)
-- Demo data for courses and FAQs so the chatbot has real content
-- to answer with immediately after setup. Run in the Supabase SQL
-- Editor AFTER college_chatbot.sql.
--
-- NOTE: Demo user accounts (admin/student) are NOT inserted here
-- because passwords must be bcrypt-hashed by the application.
-- Run `python backend/create_admin.py` after installing
-- requirements to create the first admin account safely.
-- =============================================================

-- -------------------------------------------------------------
-- Courses
-- -------------------------------------------------------------
INSERT INTO courses
(name, short_code, duration_years, total_seats, available_seats, total_fees, fees_per_year, admission_fee, eligibility_percentage, eligibility_note, scholarship_available)
VALUES
('B.Tech Computer Science and Engineering', 'CSE', 4, 120, 18, 480000, 120000, 25000, 60.00, '10+2 with Physics, Chemistry, Maths', 'Merit scholarship up to 25% for 90%+ in 12th'),
('B.Tech Electronics and Communication Engineering', 'ECE', 4, 90, 22, 440000, 110000, 25000, 55.00, '10+2 with Physics, Chemistry, Maths', 'Merit scholarship up to 20% for 90%+ in 12th'),
('B.Tech Mechanical Engineering', 'MECH', 4, 90, 30, 400000, 100000, 25000, 50.00, '10+2 with Physics, Chemistry, Maths', NULL),
('B.Tech Civil Engineering', 'CIVIL', 4, 60, 15, 380000, 95000, 25000, 50.00, '10+2 with Physics, Chemistry, Maths', NULL),
('BCA (Bachelor of Computer Applications)', 'BCA', 3, 80, 40, 240000, 80000, 15000, 50.00, '10+2 in any stream', 'Fee waiver for economically weaker section'),
('MBA (Master of Business Administration)', 'MBA', 2, 60, 0, 500000, 250000, 30000, 50.00, 'Graduation in any discipline with entrance exam score', 'Merit scholarship for CAT/MAT rank holders'),
('B.Sc Computer Science', 'BSC-CS', 3, 60, 10, 210000, 70000, 12000, 45.00, '10+2 with Science stream', NULL);

-- -------------------------------------------------------------
-- FAQs
-- -------------------------------------------------------------
INSERT INTO faqs (category, question, keywords, answer) VALUES
('admission', 'How can I apply for admission?', 'apply,admission process,how to join,registration',
 'You can apply online through our website by filling the application form, uploading your marksheets and ID proof, and paying the admission fee to confirm your seat.'),
('admission', 'What documents are required for admission?', 'documents required,documents needed,admission documents',
 'You need your 10th and 12th marksheets, transfer certificate, migration certificate, ID proof, passport-size photos, and category certificate (if applicable).'),
('fees', 'Is there any scholarship available?', 'scholarship,fee waiver,financial aid',
 'Yes, merit-based and need-based scholarships are available for eligible students. Please ask about a specific course to see its scholarship details.'),
('fees', 'Can I pay fees in installments?', 'installment,instalment,emi,pay fees in parts',
 'Yes, fees can be paid year-wise as per the college fee schedule. The admission fee must be paid upfront to confirm your seat, and it is non-refundable after confirmation.'),
('general', 'What are the college timings?', 'timings,college hours,office hours',
 'The college office is open Monday to Saturday from 9:00 AM to 5:00 PM. Classes generally run from 9:00 AM to 4:00 PM.'),
('general', 'Does the college provide hostel facilities?', 'hostel,accommodation,pg,boarding',
 'Yes, separate hostel facilities are available for boys and girls on a first-come-first-serve basis, subject to availability.'),
('general', 'Is transportation facility available?', 'bus,transport,transportation,college bus',
 'Yes, bus transportation is available covering major routes in the city. Please contact the transport office for route details and fees.');
