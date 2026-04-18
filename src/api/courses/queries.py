"""Phase 8 Step 31 — Course SQL queries."""

# ── Courses ──────────────────────────────────────────────────
LIST_COURSES = "SELECT * FROM courses ORDER BY created_at DESC LIMIT ? OFFSET ?"
LIST_COURSES_BY_INSTRUCTOR = "SELECT * FROM courses WHERE instructor_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_COURSE = "SELECT * FROM courses WHERE id = ?"
GET_COURSE_BY_SLUG = "SELECT * FROM courses WHERE slug = ?"
INSERT_COURSE = """INSERT INTO courses
    (id, org_id, instructor_id, title, slug, description, cover_image_url,
     intro_video_url, level, language, tags, price_cents, membership_tier, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_COURSE = """UPDATE courses SET
    title=?, description=?, cover_image_url=?, intro_video_url=?,
    level=?, language=?, tags=?, price_cents=?, membership_tier=?,
    status=?, updated_at=datetime('now') WHERE id=?"""
DELETE_COURSE = "DELETE FROM courses WHERE id = ?"
INCREMENT_ENROLLMENT = (
    "UPDATE courses SET enrollment_count = enrollment_count + 1 WHERE id = ?"
)
DECREMENT_ENROLLMENT = (
    "UPDATE courses SET enrollment_count = MAX(enrollment_count - 1, 0) WHERE id = ?"
)
PUBLISH_COURSE = "UPDATE courses SET status = 'published', published_at = datetime('now'), updated_at = datetime('now') WHERE id = ?"

# ── Course Modules ───────────────────────────────────────────
LIST_MODULES = "SELECT * FROM course_modules WHERE course_id = ? ORDER BY sort_order"
GET_MODULE = "SELECT * FROM course_modules WHERE id = ?"
INSERT_MODULE = """INSERT INTO course_modules
    (id, course_id, title, description, sort_order, is_free)
    VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_MODULE = """UPDATE course_modules SET
    title=?, description=?, sort_order=?, is_free=? WHERE id=?"""
DELETE_MODULE = "DELETE FROM course_modules WHERE id = ?"

# ── Course Lessons ───────────────────────────────────────────
LIST_LESSONS = "SELECT * FROM course_lessons WHERE module_id = ? ORDER BY sort_order"
LIST_LESSONS_BY_COURSE = (
    "SELECT * FROM course_lessons WHERE course_id = ? ORDER BY sort_order"
)
GET_LESSON = "SELECT * FROM course_lessons WHERE id = ?"
INSERT_LESSON = """INSERT INTO course_lessons
    (id, module_id, course_id, title, sort_order, lesson_type, article_id,
     video_url, duration_minutes, is_free)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_LESSON = """UPDATE course_lessons SET
    title=?, sort_order=?, lesson_type=?, article_id=?, video_url=?,
    duration_minutes=?, is_free=? WHERE id=?"""
DELETE_LESSON = "DELETE FROM course_lessons WHERE id = ?"

# ── Lesson Quizzes ───────────────────────────────────────────
GET_QUIZ = "SELECT * FROM lesson_quizzes WHERE id = ?"
GET_QUIZ_BY_LESSON = "SELECT * FROM lesson_quizzes WHERE lesson_id = ?"
INSERT_QUIZ = "INSERT INTO lesson_quizzes (id, lesson_id, pass_score) VALUES (?, ?, ?)"
UPDATE_QUIZ = "UPDATE lesson_quizzes SET pass_score = ? WHERE id = ?"
DELETE_QUIZ = "DELETE FROM lesson_quizzes WHERE id = ?"

# ── Quiz Questions ───────────────────────────────────────────
LIST_QUESTIONS = "SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY sort_order"
GET_QUESTION = "SELECT * FROM quiz_questions WHERE id = ?"
INSERT_QUESTION = """INSERT INTO quiz_questions
    (id, quiz_id, question_text, question_type, options, sort_order)
    VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_QUESTION = """UPDATE quiz_questions SET
    question_text=?, question_type=?, options=?, sort_order=? WHERE id=?"""
DELETE_QUESTION = "DELETE FROM quiz_questions WHERE id = ?"

# ── Course Enrollments ───────────────────────────────────────
LIST_ENROLLMENTS = "SELECT * FROM course_enrollments WHERE course_id = ? ORDER BY enrolled_at DESC LIMIT ? OFFSET ?"
LIST_ENROLLMENTS_BY_USER = "SELECT * FROM course_enrollments WHERE user_id = ? ORDER BY enrolled_at DESC LIMIT ? OFFSET ?"
GET_ENROLLMENT = "SELECT * FROM course_enrollments WHERE id = ?"
GET_ENROLLMENT_BY_USER = (
    "SELECT * FROM course_enrollments WHERE course_id = ? AND user_id = ?"
)
INSERT_ENROLLMENT = """INSERT INTO course_enrollments
    (id, course_id, user_id, status, paid_cents, payment_id)
    VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_ENROLLMENT_STATUS = "UPDATE course_enrollments SET status = ? WHERE id = ?"
COMPLETE_ENROLLMENT = "UPDATE course_enrollments SET status = 'completed', completed_at = datetime('now') WHERE id = ?"
DELETE_ENROLLMENT = "DELETE FROM course_enrollments WHERE id = ?"

# ── Lesson Progress ──────────────────────────────────────────
LIST_PROGRESS = "SELECT * FROM lesson_progress WHERE enrollment_id = ?"
GET_PROGRESS = "SELECT * FROM lesson_progress WHERE enrollment_id = ? AND lesson_id = ?"
UPSERT_PROGRESS = """INSERT INTO lesson_progress
    (enrollment_id, lesson_id, status, progress_pct, quiz_score, last_viewed_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    ON CONFLICT(enrollment_id, lesson_id) DO UPDATE SET
    status=excluded.status, progress_pct=excluded.progress_pct,
    quiz_score=excluded.quiz_score, last_viewed_at=datetime('now')"""
COMPLETE_PROGRESS = """INSERT INTO lesson_progress
    (enrollment_id, lesson_id, status, progress_pct, completed_at, last_viewed_at)
    VALUES (?, ?, 'completed', 100, datetime('now'), datetime('now'))
    ON CONFLICT(enrollment_id, lesson_id) DO UPDATE SET
    status='completed', progress_pct=100, completed_at=datetime('now'),
    last_viewed_at=datetime('now')"""

# ── Certificates ─────────────────────────────────────────────
LIST_CERTIFICATES_BY_USER = (
    "SELECT * FROM certificates WHERE user_id = ? ORDER BY issued_at DESC"
)
LIST_CERTIFICATES_BY_COURSE = (
    "SELECT * FROM certificates WHERE course_id = ? ORDER BY issued_at DESC"
)
GET_CERTIFICATE = "SELECT * FROM certificates WHERE id = ?"
GET_CERTIFICATE_BY_USER_COURSE = (
    "SELECT * FROM certificates WHERE course_id = ? AND user_id = ?"
)
INSERT_CERTIFICATE = """INSERT INTO certificates
    (id, course_id, user_id, enrollment_id, certificate_url)
    VALUES (?, ?, ?, ?, ?)"""
DELETE_CERTIFICATE = "DELETE FROM certificates WHERE id = ?"
