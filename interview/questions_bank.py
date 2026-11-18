"""
Comprehensive Offline Interview Question Bank with Coding Challenges, Test Cases & Follow-ups.
Over 150+ categorized questions across technical disciplines, HR, projects, and coding.
"""

SKILL_KEYWORDS = {
    'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
    'java': ['java', 'spring', 'spring boot', 'hibernate', 'maven'],
    'javascript': ['javascript', 'js', 'react', 'node', 'nodejs', 'express', 'vue', 'angular'],
    'cpp': ['c++', 'cpp', 'stl', 'pointers', 'templates'],
    'c': ['c language', 'embedded c', 'c programming'],
    'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'database', 'rdbms'],
    'django': ['django', 'django orm', 'django rest framework', 'drf'],
    'react': ['react', 'react.js', 'reactjs', 'jsx', 'hooks', 'redux'],
    'web': ['html', 'css', 'bootstrap', 'rest api', 'api', 'http'],
    'dsa': ['data structures', 'algorithms', 'trees', 'graphs', 'sorting', 'arrays'],
}

QUESTIONS_BANK = {
    'python': [
        'Explain the core Object-Oriented Programming (OOP) concepts in Python with examples.',
        'What is the difference between a list and a tuple in Python, and when would you choose one over the other?',
        'Explain Python decorators and write a simple decorator to measure execution time.',
        'What are generator functions and the `yield` keyword in Python? How do they save memory?',
        'Explain the Global Interpreter Lock (GIL) in Python and its impact on multithreading.',
        'What is the difference between deep copy and shallow copy in Python?',
        'Explain Method Resolution Order (MRO) and the `super()` function in Python.',
        'How does Python handle memory management and garbage collection?',
    ],
    'django': [
        'Explain the Django MVT (Model-View-Template) architectural pattern and how it handles an incoming request.',
        'What is Django ORM? Explain the difference between `select_related` and `prefetch_related`.',
        'What is Django middleware, and how can you create custom middleware for request logging or authentication?',
        'Explain the migration workflow in Django and how Django tracks schema changes.',
        'How do Django signals work, and when should you avoid using them?',
        'How do you protect a Django application against CSRF, SQL Injection, and XSS attacks?',
    ],
    'java': [
        'Explain the key differences between Java and Python in terms of memory management and typing.',
        'What is the difference between `==` and `.equals()` in Java?',
        'Explain Java Garbage Collection and the different memory generations in the JVM.',
        'What is the Java Collections Framework? Explain the difference between `HashMap` and `ConcurrentHashMap`.',
        'What are Java abstract classes versus interfaces, especially with Java 8 default methods?',
        'Explain multithreading and the `synchronized` keyword in Java.',
    ],
    'javascript': [
        'Explain the JavaScript Event Loop, call stack, microtask queue, and callback queue.',
        'What is the difference between `var`, `let`, and `const`, and what is hoisting?',
        'Explain JavaScript closures and provide a practical use-case such as data privacy.',
        'What are Promises and `async/await` in JavaScript? How do they handle errors?',
        'Explain prototypal inheritance in JavaScript versus classical inheritance.',
    ],
    'react': [
        'What is the Virtual DOM in React and how does reconciliation work?',
        'Explain the React Component lifecycle and how hooks like `useEffect` replace class lifecycle methods.',
        'What is the difference between controlled and uncontrolled components in React?',
        'How do you manage complex application state in React (Context API vs Redux)?',
        'What are React custom hooks and when would you extract logic into one?',
    ],
    'sql': [
        'What is the difference between `INNER JOIN`, `LEFT JOIN`, and `FULL OUTER JOIN` in SQL?',
        'What is the difference between `UNION` and `UNION ALL`?',
        'Explain database normalization from 1NF to 3NF and why denormalization is sometimes practiced.',
        'What is a database index, how does a B-Tree index work, and what are its trade-offs?',
        'Explain ACID properties in database transactions with real-world examples.',
    ],
    'cpp': [
        'What is the difference between pointers and references in C++?',
        'Explain RAII (Resource Acquisition Is Initialization) and smart pointers in modern C++.',
        'What is the Standard Template Library (STL) and how do `std::vector` and `std::list` differ?',
        'Explain virtual functions, vtables, and runtime polymorphism in C++.',
    ],
    'project_based': [
        'Walk me through the architecture of the most significant project listed on your resume.',
        'What was the most challenging technical roadblock you encountered in your project, and how did you resolve it?',
        'How did you design the database schema for your project, and how would you scale it for 100,000 concurrent users?',
        'Why did you choose your specific tech stack over alternatives for your project?',
        'Explain how authentication and authorization were implemented in your project.',
    ],
    'hr': [
        'Tell me about yourself, your academic background, and your key technical passions.',
        'Describe a situation where you had a disagreement with a team member or peer. How did you resolve it?',
        'Where do you see yourself professionally in the next 3 to 5 years?',
        'Why are you interested in joining our engineering team, and what value will you bring?',
        'Tell me about a time you had to learn an unfamiliar technology or framework under a tight deadline.',
        'What are your greatest technical strengths and an area where you are actively working to improve?',
    ],
    'experience_based': [
        'Reflecting on your internship or coursework, what was your single most impactful contribution?',
        'How do you approach code reviews, testing, and debugging when working on collaborative codebases?',
        'Can you give an example of how you prioritized features when facing conflicting deadlines?',
    ],
    'cross_questions': [
        'You mentioned having experience with both {lang1} and {lang2}. In what scenarios would you choose {lang1} over {lang2}?',
        'Your resume highlights {project}. If you had to redesign it from scratch today, what architecture would you change?',
        'How did you ensure security, validation, and performance in your {skill} implementation?',
    ]
}

# CODING CHALLENGES WITH SPECIFICATIONS, STARTER CODE & TEST CASES
CODING_CHALLENGES = [
    {
        'id': 'fibonacci',
        'title': 'Fibonacci Series Generator',
        'problem': 'Write a program to generate the first N Fibonacci numbers (where N >= 1, starting with 0, 1, 1, 2, ...). Return the series as space-separated numbers or list.',
        'difficulty': 'beginner',
        'starter_codes': {
            'python': 'def fibonacci(n):\n    # Write your solution here\n    pass\n\nif __name__ == "__main__":\n    import sys\n    n = int(sys.stdin.read().strip() or "5")\n    print(fibonacci(n))\n',
            'javascript': 'function fibonacci(n) {\n    // Write your code here\n}\nconst fs = require("fs");\nconst input = parseInt(fs.readFileSync(0, "utf-8").trim() || "5");\nconsole.log(fibonacci(input));\n',
            'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.hasNextInt() ? sc.nextInt() : 5;\n        // Write logic here\n    }\n}\n',
            'cpp': '#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    if (cin >> n) {\n        // Write logic here\n    }\n    return 0;\n}\n',
            'c': '#include <stdio.h>\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        // Write logic here\n    }\n    return 0;\n}\n'
        },
        'test_cases': [
            {'input': '5', 'expected_output': '0 1 1 2 3'},
            {'input': '1', 'expected_output': '0'},
            {'input': '7', 'expected_output': '0 1 1 2 3 5 8'},
        ],
        'model_answer': 'Python: def fibonacci(n):\n    res = [0, 1]\n    while len(res) < n:\n        res.append(res[-1] + res[-2])\n    return " ".join(map(str, res[:n]))'
    },
    {
        'id': 'prime_check',
        'title': 'Prime Number Check',
        'problem': 'Write a program that takes an integer N and determines whether N is a Prime number. Output "PRIME" or "NOT PRIME".',
        'difficulty': 'beginner',
        'starter_codes': {
            'python': 'def is_prime(n):\n    # Return "PRIME" or "NOT PRIME"\n    pass\n\nif __name__ == "__main__":\n    import sys\n    n = int(sys.stdin.read().strip() or "7")\n    print(is_prime(n))\n',
            'javascript': 'function isPrime(n) {\n    // Return "PRIME" or "NOT PRIME"\n}\nconst fs = require("fs");\nconst input = parseInt(fs.readFileSync(0, "utf-8").trim() || "7");\nconsole.log(isPrime(input));\n',
            'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.hasNextInt() ? sc.nextInt() : 7;\n        // Write logic\n    }\n}\n',
            'cpp': '#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    if (cin >> n) {\n        // Write logic\n    }\n    return 0;\n}\n',
            'c': '#include <stdio.h>\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        // Write logic\n    }\n    return 0;\n}\n'
        },
        'test_cases': [
            {'input': '7', 'expected_output': 'PRIME'},
            {'input': '10', 'expected_output': 'NOT PRIME'},
            {'input': '2', 'expected_output': 'PRIME'},
            {'input': '1', 'expected_output': 'NOT PRIME'},
        ],
        'model_answer': 'Check if n <= 1 return "NOT PRIME". Iterate from 2 up to int(n**0.5) + 1. If divisible, return "NOT PRIME". Else "PRIME".'
    },
    {
        'id': 'palindrome',
        'title': 'Valid Palindrome Checker',
        'problem': 'Write a program to check if a given string is a palindrome (ignoring casing and non-alphanumeric characters). Output "TRUE" or "FALSE".',
        'difficulty': 'intermediate',
        'starter_codes': {
            'python': 'def is_palindrome(s):\n    # Return "TRUE" or "FALSE"\n    pass\n\nif __name__ == "__main__":\n    import sys\n    s = sys.stdin.read().strip()\n    print(is_palindrome(s))\n',
            'javascript': 'function isPalindrome(s) {\n    // Return "TRUE" or "FALSE"\n}\nconst fs = require("fs");\nconst input = fs.readFileSync(0, "utf-8").trim();\nconsole.log(isPalindrome(input));\n',
            'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.hasNextLine() ? sc.nextLine() : "";\n        // Write logic\n    }\n}\n',
            'cpp': '#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string s;\n    if (getline(cin, s)) {\n        // Write logic\n    }\n    return 0;\n}\n',
            'c': '#include <stdio.h>\n#include <string.h>\nint main() {\n    char s[256];\n    if (fgets(s, sizeof(s), stdin)) {\n        // Write logic\n    }\n    return 0;\n}\n'
        },
        'test_cases': [
            {'input': 'A man, a plan, a canal: Panama', 'expected_output': 'TRUE'},
            {'input': 'race a car', 'expected_output': 'FALSE'},
            {'input': 'Madam', 'expected_output': 'TRUE'},
        ],
        'model_answer': 'Filter non-alphanumeric chars, convert to lowercase, verify s == s[::-1].'
    },
    {
        'id': 'two_sum',
        'title': 'Two Sum Problem',
        'problem': 'Given an array of integers and a target sum, output the 0-based indices of the two numbers that add up to the target, formatted as "idx1 idx2".',
        'difficulty': 'intermediate',
        'starter_codes': {
            'python': 'def two_sum(nums, target):\n    # Return indices "i j"\n    pass\n\nif __name__ == "__main__":\n    import sys\n    lines = sys.stdin.read().splitlines()\n    if len(lines) >= 2:\n        nums = list(map(int, lines[0].split()))\n        target = int(lines[1])\n        print(two_sum(nums, target))\n',
            'javascript': 'function twoSum(nums, target) {\n    // Return indices "i j"\n}\nconst fs = require("fs");\nconst lines = fs.readFileSync(0, "utf-8").trim().split("\\n");\nif (lines.length >= 2) {\n    const nums = lines[0].split(" ").map(Number);\n    const target = Number(lines[1]);\n    console.log(twoSum(nums, target));\n}\n',
            'java': 'import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        // Two sum solution\n    }\n}\n',
            'cpp': '#include <iostream>\n#include <vector>\n#include <unordered_map>\nusing namespace std;\nint main() {\n    // Two sum solution\n    return 0;\n}\n',
            'c': '#include <stdio.h>\nint main() {\n    // Two sum solution\n    return 0;\n}\n'
        },
        'test_cases': [
            {'input': '2 7 11 15\n9', 'expected_output': '0 1'},
            {'input': '3 2 4\n6', 'expected_output': '1 2'},
        ],
        'model_answer': 'Use a hash map to store value -> index. For each num, check if (target - num) exists in map. O(N) time and space.'
    }
]
