import json
import asyncio
from typing import Dict, List
from .transcript_processor import TranscriptProcessor
from .groq_client import GroqClient
import sys
import re

# Remove extract_main_subject and all main_subject logic

class CourseGenerator:
    def __init__(self, groq_client: GroqClient, processor: TranscriptProcessor):
        self.client = groq_client
        self.processor = processor
    
    async def generate_complete_course(self, transcript_json: Dict, video_title: str = "Unknown Title") -> Dict:
        """
        Main method to generate complete course from transcript and video title
        """
        content = transcript_json["content"]
        token_count = self.processor.count_tokens(content)
        
        if token_count <= 6000: # Direct processing
            return await self._direct_course_generation(content, video_title)
        else:  # Micro-chunking approach
            return await self._chunked_course_generation(content, video_title)
    
    async def _direct_course_generation(self, content: str, video_title: str) -> Dict:
        """
        Generate course directly for shorter transcripts
        """
        # Step 1: Get detailed analysis data from DeepSeek
        analysis_prompt = f"""
Analyze this YouTube video transcript and create comprehensive educational content.

Provide detailed, well-structured content with:
- Main topics that are specific and descriptive
- Key concepts with detailed explanations (2-3 sentences each)
- Examples and demonstrations with practical details
- Quiz questions with 4 realistic answer options and correct answers
- Learning objectives that are specific and measurable

Return a JSON object with this exact structure:
{{
  "analysis": {{
    "main_topics": [
      "Specific topic title with clear focus",
      "Another specific topic with clear focus"
    ],
    "key_concepts": [
      "Detailed concept explanation with practical details and examples. This should be comprehensive enough to teach the concept thoroughly.",
      "Another detailed concept with real-world applications and step-by-step explanations."
    ],
    "examples_demonstrations": [
      "Detailed example with step-by-step explanation, code snippets if applicable, and practical implementation details.",
      "Another comprehensive example with real-world scenarios and detailed walkthrough."
    ],
    "quiz_questions": [
      {{
        "question": "Specific question about the content",
        "options": [
          "Realistic answer option 1",
          "Realistic answer option 2", 
          "Realistic answer option 3",
          "Realistic answer option 4"
        ],
        "correct_answer": "The correct answer text",
        "explanation": "Detailed explanation of why this answer is correct and why others are wrong"
      }}
    ],
    "learning_objectives": [
      "Specific, measurable learning objective that clearly states what the learner will be able to do",
      "Another specific objective with clear success criteria"
    ]
  }}
}}

Transcript:
{content}
"""
        
        try:
            print(f"🔍 DEBUG: Getting analysis from DeepSeek...")
            analysis_response = await self.client.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=8000,  # Increased for better content generation
                temperature=0.3,   # Slightly higher for more creative content
                response_format={"type": "json_object"}
            )
            
            print(f"🔍 DEBUG: Analysis received, converting to course structure...")
            analysis_data = json.loads(analysis_response)
            
            # Step 2: Convert analysis to structured course
            course_data = self._convert_analysis_to_course(analysis_data, video_title, content)
            print(f"✅ DEBUG: Course structure generated successfully")
            return course_data
            
        except Exception as e:
            print(f"❌ DEBUG: Error in course generation: {str(e)}")
    
    async def _chunked_course_generation(self, content: str, video_title: str) -> Dict:
        """
        Generate course using micro-chunking for long transcripts
        """
        chunks = self.processor.create_semantic_micro_chunks(content)
        
        # Process chunks sequentially
        chunk_analyses = []
        for i, chunk in enumerate(chunks):
            result = await self._analyze_chunk(chunk, i+1, len(chunks), video_title)
            chunk_analyses.append(result)
            await asyncio.sleep(2)  # Reduced to 2s since we use llama-3.1-8b-instant now
        
        # Filter out irrelevant or empty analyses
        # No longer filtering by main_subject, as it's not enforced
        if not chunk_analyses:
            return {"error": f"No relevant content found for subject. Please provide a more focused transcript."}

        # Synthesize final course
        return await self._synthesize_course_from_chunks(chunk_analyses, video_title)
    
    async def _analyze_chunk(self, chunk: str, chunk_num: int, total_chunks: int, video_title: str) -> Dict:
        print(f"\n--- Sending chunk {chunk_num}/{total_chunks} ---\n{chunk[:500]}\n...\n", file=sys.stderr)
        prompt = f"""
Analyze this segment ({chunk_num}/{total_chunks}) of an educational video transcript.

Extract and return JSON with detailed content:
- Main topics covered (specific and descriptive)
- Key concepts explained (detailed explanations)
- Examples or demonstrations (practical details)
- Quiz questions with 4 realistic options and correct answers
- Learning objectives (specific and measurable)

Return JSON with this structure:
{{
  "main_topics": ["Specific topic 1", "Specific topic 2"],
  "key_concepts": ["Detailed concept explanation with examples"],
  "examples_demonstrations": ["Detailed example with step-by-step explanation"],
  "quiz_questions": [
    {{
      "question": "Specific question about the content",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "The correct answer",
      "explanation": "Why this answer is correct"
    }}
  ],
  "learning_objectives": ["Specific, measurable objective"]
}}

Segment: {chunk}
"""
        print(f"Prompt for chunk {chunk_num}: {prompt[:300]}...", file=sys.stderr)
        
        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"},
                model="llama-3.1-8b-instant"
            )
            
            return {
                "chunk_number": chunk_num,
                "analysis": json.loads(response),
                "original_text": chunk
            }
        except Exception:
            return {
                "chunk_number": chunk_num,
                "analysis": {"topics": ["Content analysis unavailable"]},
                "original_text": chunk
            }
    
    async def _synthesize_course_from_chunks(self, chunk_analyses: List[Dict], video_title: str) -> Dict:
        """
        Combine chunk analyses into final course structure
        """
        # Combine all analyses into a single analysis structure
        combined_main_topics = []
        combined_key_concepts = []
        combined_examples = []
        combined_quiz_questions = []
        combined_learning_objectives = []
        
        for chunk in chunk_analyses:
            analysis = chunk.get("analysis", {})
            combined_main_topics.extend(analysis.get("main_topics", []))
            combined_key_concepts.extend(analysis.get("key_concepts", []))
            combined_examples.extend(analysis.get("examples_demonstrations", []))
            combined_quiz_questions.extend(analysis.get("quiz_questions", []))  # Updated field name
            combined_learning_objectives.extend(analysis.get("learning_objectives", []))
        
        # Remove duplicates while preserving order
        combined_main_topics = list(dict.fromkeys(combined_main_topics))
        combined_key_concepts = list(dict.fromkeys(combined_key_concepts))
        combined_examples = list(dict.fromkeys(combined_examples))
        # For quiz questions, we need to handle the new structure
        unique_quiz_questions = []
        seen_questions = set()
        for quiz in combined_quiz_questions:
            question_text = quiz.get("question", "")
            if question_text not in seen_questions:
                unique_quiz_questions.append(quiz)
                seen_questions.add(question_text)
        combined_quiz_questions = unique_quiz_questions
        combined_learning_objectives = list(dict.fromkeys(combined_learning_objectives))
        
        # Create combined analysis structure
        combined_analysis = {
            "analysis": {
                "main_topics": combined_main_topics,
                "key_concepts": combined_key_concepts,
                "examples_demonstrations": combined_examples,
                "potential_quiz_questions": combined_quiz_questions,
                "learning_objectives": combined_learning_objectives
            }
        }
        
        # Use the same conversion method as direct generation
        return self._convert_analysis_to_course(combined_analysis, video_title, "Long course content")
    
    def _convert_analysis_to_course(self, analysis_data: Dict, video_title: str, content: str) -> Dict:
        """
        Convert analysis data to structured course format
        """
        analysis = analysis_data.get("analysis", {})
        
        # Extract data from analysis
        main_topics = analysis.get("main_topics", [])
        key_concepts = analysis.get("key_concepts", [])
        examples = analysis.get("examples_demonstrations", [])
        quiz_questions = analysis.get("quiz_questions", [])  # New structure
        learning_objectives = analysis.get("learning_objectives", [])
        
        # Generate course info
        course_title = self._generate_course_title(main_topics, video_title)
        total_lessons = max(len(main_topics), 3)  # Minimum 3 lessons
        
        # Generate lessons from main topics
        lessons = []
        for i, topic in enumerate(main_topics):
            lesson = self._create_lesson_from_topic(
                topic, i + 1, key_concepts, examples, quiz_questions, learning_objectives
            )
            lessons.append(lesson)
        
        # If we have fewer than 3 lessons, create additional ones from concepts
        if len(lessons) < 3:
            remaining_concepts = key_concepts[len(lessons):]
            for i, concept in enumerate(remaining_concepts[:3 - len(lessons)]):
                lesson = self._create_lesson_from_concept(
                    concept, len(lessons) + i + 1, examples, quiz_questions
                )
                lessons.append(lesson)
        
        return {
            "courseInfo": {
                "title": course_title,
                "subtitle": f"Comprehensive course on {course_title.lower()}",
                "duration": self._estimate_duration(len(lessons)),
                "totalLessons": len(lessons)
            },
            "videoSource": {
                "url": "original_video_url"
            },
            "lessons": lessons,
            "finalExam": {
                "enabled": True,
                "prerequisiteCompletion": 100,
                "timeLimit": "1h 30min",
                "questionCount": min(len(quiz_questions), 10),
                "passingScore": 70,
                "examType": "application_based"
            }
        }
    
    def _generate_course_title(self, main_topics: List[str], video_title: str) -> str:
        """Generate course title from main topics or video title"""
        if main_topics:
            # Use the first main topic as course title
            return main_topics[0]
        elif video_title and video_title != "Unknown Title":
            return video_title
        else:
            return "Comprehensive Learning Course"
    
    def _estimate_duration(self, lesson_count: int) -> str:
        """Estimate course duration based on lesson count"""
        total_minutes = lesson_count * 15  # 15 minutes per lesson
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}min"
        else:
            return f"{minutes}min"
    
    def _create_lesson_from_topic(self, topic: str, lesson_id: int, key_concepts: List[str], 
                                 examples: List[str], quiz_questions: List[Dict], 
                                 learning_objectives: List[str]) -> Dict:
        """Create a lesson from a main topic"""
        
        # Calculate timestamp based on lesson position
        start_time = self._calculate_timestamp(lesson_id - 1)
        end_time = self._calculate_timestamp(lesson_id)
        
        # Find related concepts and examples
        related_concepts = self._find_related_content(topic, key_concepts)
        related_examples = self._find_related_content(topic, examples)
        
        # Create sections
        sections = []
        
        # Concept section
        if related_concepts:
            sections.append({
                "title": f"Understanding {topic}",
                "type": "concept",
                "points": [
                    {
                        "subtitle": concept[:50] + "..." if len(concept) > 50 else concept,
                        "content": concept
                    } for concept in related_concepts[:3]  # Limit to 3 concepts
                ]
            })
        
        # Example section
        if related_examples:
            sections.append({
                "title": f"Examples and Demonstrations",
                "type": "example",
                "points": [
                    {
                        "subtitle": example[:50] + "..." if len(example) > 50 else example,
                        "content": example
                    } for example in related_examples[:2]  # Limit to 2 examples
                ]
            })
        
        # Generate quizzes for this lesson
        lesson_quizzes = self._generate_lesson_quizzes(topic, quiz_questions, lesson_id)
        
        return {
            "id": lesson_id,
            "title": topic,
            "subtitle": f"Learn about {topic.lower()}",
            "type": "video",
            "videoMeta": {
                "start": start_time,
                "end": end_time
            },
            "completed": False,
            "current": False,
            "content": {
                "introduction": f"In this lesson, we'll explore {topic.lower()} and its key concepts.",
                "sections": sections,
                "conclusion": f"You've now learned about {topic.lower()}. Practice these concepts to reinforce your understanding."
            },
            "quizzes": lesson_quizzes
        }
    
    def _create_lesson_from_concept(self, concept: str, lesson_id: int, 
                                   examples: List[str], quiz_questions: List[Dict]) -> Dict:
        """Create a lesson from a key concept"""
        
        start_time = self._calculate_timestamp(lesson_id - 1)
        end_time = self._calculate_timestamp(lesson_id)
        
        # Generate quizzes for this lesson
        lesson_quizzes = self._generate_lesson_quizzes(concept, quiz_questions, lesson_id)
        
        return {
            "id": lesson_id,
            "title": concept[:50] + "..." if len(concept) > 50 else concept,
            "subtitle": f"Understanding {concept.lower()[:30]}...",
            "type": "video",
            "videoMeta": {
                "start": start_time,
                "end": end_time
            },
            "completed": False,
            "current": False,
            "content": {
                "introduction": f"This lesson covers {concept.lower()}.",
                "sections": [
                    {
                        "title": "Key Concept",
                        "type": "concept",
                        "points": [
                            {
                                "subtitle": "Main Concept",
                                "content": concept
                            }
                        ]
                    }
                ],
                "conclusion": f"You've learned about {concept.lower()[:30]}..."
            },
            "quizzes": lesson_quizzes
        }
    
    def _calculate_timestamp(self, lesson_index: int) -> str:
        """Calculate timestamp for lesson based on index"""
        minutes = lesson_index * 15  # 15 minutes per lesson
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:00"
    
    def _find_related_content(self, topic: str, content_list: List[str]) -> List[str]:
        """Find content related to a specific topic"""
        related = []
        topic_lower = topic.lower()
        
        for content in content_list:
            if any(word in content.lower() for word in topic_lower.split()):
                related.append(content)
        
        return related[:3]  # Return up to 3 related items
    
    def _generate_lesson_quizzes(self, topic: str, quiz_questions: List[Dict], lesson_id: int) -> List[Dict]:
        """Generate quizzes for a specific lesson"""
        quizzes = []
        
        # Find questions related to this topic
        related_questions = self._find_related_quiz_questions(topic, quiz_questions)
        
        # Generate 2-3 quizzes per lesson
        quiz_count = min(len(related_questions), 3)
        
        for i in range(quiz_count):
            if i < len(related_questions):
                quiz_data = related_questions[i]
                quiz = {
                    "id": lesson_id * 10 + i + 1,
                    "question": quiz_data.get("question", f"Question about {topic}"),
                    "type": "multiple_choice",
                    "options": quiz_data.get("options", ["Option A", "Option B", "Option C", "Option D"]),
                    "correctAnswer": self._find_correct_answer_index(quiz_data),
                    "answer": quiz_data.get("correct_answer", "Correct answer"),
                    "explanation": quiz_data.get("explanation", f"This question tests your understanding of {topic.lower()}.")
                }
                quizzes.append(quiz)
        
        # If we don't have enough related questions, create generic ones
        while len(quizzes) < 2:
            quiz = {
                "id": lesson_id * 10 + len(quizzes) + 1,
                "question": f"What is the main concept of {topic.lower()}?",
                "type": "multiple_choice",
                "options": [
                    "A fundamental principle",
                    "An advanced technique", 
                    "A basic concept",
                    "A complex theory"
                ],
                "correctAnswer": 2,  # "A basic concept"
                "answer": "A basic concept",
                "explanation": f"This question evaluates your understanding of {topic.lower()}."
            }
            quizzes.append(quiz)
        
        return quizzes
    
    def _find_related_quiz_questions(self, topic: str, quiz_questions: List[Dict]) -> List[Dict]:
        """Find quiz questions related to a specific topic"""
        related = []
        topic_lower = topic.lower()
        
        for quiz in quiz_questions:
            question_text = quiz.get("question", "").lower()
            if any(word in question_text for word in topic_lower.split()):
                related.append(quiz)
        
        return related[:3]  # Return up to 3 related questions
    
    def _find_correct_answer_index(self, quiz_data: Dict) -> int:
        """Find the index of the correct answer in the options"""
        correct_answer = quiz_data.get("correct_answer", "")
        options = quiz_data.get("options", [])
        
        for i, option in enumerate(options):
            if option.lower() == correct_answer.lower():
                return i
        
        # If not found, return 0 as default
        return 0