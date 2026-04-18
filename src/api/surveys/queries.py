INSERT_SURVEY = (
    "INSERT INTO surveys (id, title, description, author_id, article_id, is_active)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)

INSERT_QUESTION = (
    "INSERT INTO survey_questions (id, survey_id, question_text, question_type, options_json, is_required, sort_order)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

INSERT_RESPONSE = (
    "INSERT INTO survey_responses (id, survey_id, question_id, user_id, session_id, answer_text, answer_option_index)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

GET_SURVEY = "SELECT * FROM surveys WHERE id = ? AND is_active = 1"

GET_QUESTIONS_FOR_SURVEY = (
    "SELECT * FROM survey_questions WHERE survey_id = ? ORDER BY sort_order ASC"
)

GET_SURVEYS_BY_AUTHOR = "SELECT * FROM surveys WHERE author_id = ? AND is_active = 1"

CHECK_IF_USER_RESPONDED = (
    "SELECT COUNT(*) as c FROM survey_responses WHERE question_id = ? AND user_id = ?"
)

CHECK_IF_SESSION_RESPONDED = "SELECT COUNT(*) as c FROM survey_responses WHERE question_id = ? AND session_id = ?"
