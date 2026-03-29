class Prompts:
    TOPIC_EXTRACTION = """
You are an expert course architect.

### 🎯 Goal
Analyze the provided transcript and extract a logically ordered list of main topics covered.

### ⚠️ Rules
1. Topics must be distinct and sequential based on the transcript.
2. Provide a short summary of each topic.
3. Extract accurate start and end timestamps (if provided in transcript structure, else approximate relative flow).
4. Output MUST be strictly JSON mapping to the requested schema.

### 📦 Transcript:
{transcript}
"""

    LESSON_PLANNER = """
You are an expert curriculum designer.

### 🎯 Goal
Convert the following extracted topics into structured lesson plans.

### ⚠️ Rules
1. Create a clear, engaging title and subtitle for each lesson.
2. Make sure the lesson count equals the topic count (or merges smoothly).
3. Do not generate the actual content yet, just the outline mapping the `title`, `subtitle`, and `videoMeta`.
4. Return strictly valid JSON formatted to the `LessonPlan` schema.

### 📦 Topics:
{topics_json}
"""

    CONTENT_GENERATOR = """
You are an expert educational content writer.

### 🎯 Goal
Generate detailed, comprehensive, and engaging lesson content for the topic: "{lesson_title}".

### ⚠️ Rules
1. Use the provided transcript segment as ground truth. Do not hallucinate outside facts.
2. Structure the content strictly into:
   - introduction (1-2 paragraphs)
   - sections (Mix of 'concept' and 'example' types)
   - conclusion (Short summary)
3. For each section, provide specific points with subtitles and detailed explanations.
4. If a concept is abstract, follow it with an 'example' section to provide real-world context.
5. All text MUST be generated in CLEAR ENGLISH, regardless of original language.
6. Return strictly valid JSON formatted to the `LessonContent` schema.

### 📦 Topic Context & Constraints:
Lesson Subtitle: {lesson_subtitle}

### 📦 Source Transcript Segment:
{transcript_segment}
"""

    QUIZ_GENERATOR = """
You are an expert educational evaluator.

### 🎯 Goal
Generate multiple-choice questions (MCQs) to test understanding of the following lesson content.

### ⚠️ Rules
1. Generate exactly 3 questions.
2. Mix question types: 1 conceptual (why/how), 1 scenario-based, 1 tricky/misconception.
3. Each question MUST have exactly 4 options.
4. Specify the `correctAnswer` strictly as an integer index (0-3).
5. Provide a detailed explanation for why the answer is correct.
6. Return strictly valid JSON array of `Quiz` objects format.

### 📦 Lesson Content:
{lesson_content}
"""

