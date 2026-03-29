from typing import List, Dict, Any
from models.pipeline_schemas import (
    FinalCourse, CourseInfo, VideoSource, FinalExam, Lesson, 
    LessonContent, QuizList, BaseLessonOutline, VideoMeta
)

class CourseAssembler:
    @staticmethod
    def assemble_final_course(
        video_url: str,
        video_title: str,
        lesson_outlines: List[BaseLessonOutline],
        lesson_contents: List[LessonContent],
        lesson_quizzes: List[QuizList]
    ) -> FinalCourse:
        """
        Assembles all discrete pipeline elements into a unified strictly typed FinalCourse JSON format.
        Throws a Pydantic Validation error if anything doesn't strictly adhere.
        """
        total_lessons = len(lesson_outlines)
        
        course_info = CourseInfo(
            title=video_title if video_title and video_title != "Unknown Title" else "Comprehensive Learning Course",
            subtitle=f"Master {video_title} through structured, hands-on lessons.",
            duration=CourseAssembler._estimate_duration(total_lessons),
            totalLessons=total_lessons
        )

        completed_lessons: List[Lesson] = []
        total_quiz_count = 0

        # Zip assumes all lists are symmetrically populated sequentially
        for i, (outline, content, quiz_list) in enumerate(zip(lesson_outlines, lesson_contents, lesson_quizzes)):
            lesson_id = i + 1
            
            # Reassign quiz IDs sequentially across the course or within lesson offsets
            quizzes = quiz_list.quizzes
            for j, quiz in enumerate(quizzes):
                quiz.id = (lesson_id * 10) + j + 1
            
            total_quiz_count += len(quizzes)
            
            lesson = Lesson(
                id=lesson_id,
                title=outline.title,
                subtitle=outline.subtitle,
                type="video",
                videoMeta=outline.videoMeta,
                completed=False,
                current=(i == 0), # Assign first lesson as current
                content=content,
                quizzes=quizzes
            )
            completed_lessons.append(lesson)

        final_exam = FinalExam(
            enabled=True,
            prerequisiteCompletion=100,
            timeLimit="1h 30min",
            questionCount=min(total_quiz_count, 15), # Cap final exam questions if needed or use total.
            passingScore=70,
            examType="application_based"
        )
        
        video_source = VideoSource(url=video_url)

        final_course = FinalCourse(
            courseInfo=course_info,
            videoSource=video_source,
            lessons=completed_lessons,
            finalExam=final_exam
        )

        return final_course

    @staticmethod
    def _estimate_duration(lesson_count: int) -> str:
        """Estimate course duration based on 15 mins per lesson."""
        total_minutes = lesson_count * 15
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"
