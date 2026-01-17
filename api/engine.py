import random
import uuid

class QuizEngine:
    def __init__(self, banks):
        self.banks = banks          # All question banks
        self.sessions = {}          # Active user sessions

    def start_session(self, bank, count, start=0, end=None):
        if bank not in self.banks:
            raise ValueError("Invalid bank name")

        questions = self.banks[bank]
        total = len(questions)
        start = max(0, start)
        end = min(end if end is not None else total, total)

        pool = questions[start:end]
        if count > len(pool):
            count = len(pool)

        selected = random.sample(pool, count)
        session_id = str(uuid.uuid4())  # Unique session ID

        # Store session
        self.sessions[session_id] = {
            "bank": bank,
            "questions": selected,
            "index": 0,
            "score": 0,
            "total": count
        }
        return session_id

    def get_question(self, session_id):
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        if session["index"] >= session["total"]:
            return None  # Quiz finished

        q = session["questions"][session["index"]]
        # Shuffle options each time
        options = list(q["options"].values())
        random.shuffle(options)

        return {
            "question": q["question"],
            "options": options,
            "index": session["index"] + 1,
            "total": session["total"]
        }

    def submit_answer(self, session_id, answer_text):
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        q = session["questions"][session["index"]]
        correct_answer = q["options"][q["answer"]]

        correct = answer_text == correct_answer
        if correct:
            session["score"] += 1

        session["index"] += 1
        finished = session["index"] >= session["total"]

        return {
            "correct": correct,
            "score": session["score"],
            "finished": finished
        }

    def end_session(self, session_id):
        session = self.sessions.pop(session_id, None)
        if not session:
            raise ValueError("Session not found")

        return {
            "final_score": session["score"],
            "total": session["total"]
        }
