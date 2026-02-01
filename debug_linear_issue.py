"""
Debug script để kiểm tra tại sao linear scale questions không được điền
"""
import json
import sys

def check_extracted_questions(json_file='extracted_form_test.json'):
    """Kiểm tra questions đã được extract"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("="*80)
        print("📋 EXTRACTED QUESTIONS:")
        print("="*80)
        
        questions = data.get('questions', [])
        print(f"\nTotal questions: {len(questions)}")
        
        for i, q in enumerate(questions):
            q_type = q.get('type', 'unknown')
            title = q.get('title', '')
            options = q.get('options', [])
            required = q.get('required', False)
            
            print(f"\n[{i}] Type: {q_type} | Required: {required}")
            print(f"    Title: {title[:80]}...")
            
            if q_type == 'linear_scale':
                print(f"    ✅ LINEAR SCALE detected!")
                print(f"    Options: {options}")
            elif 'linear' in title.lower() or 'scale' in title.lower():
                print(f"    ⚠️  Title có 'linear/scale' nhưng type = {q_type}")
                print(f"    Options: {options}")
            
            if required and not options:
                print(f"    ❌ REQUIRED but no options!")
        
        # Kiểm tra answers
        print("\n" + "="*80)
        print("📝 SAVED ANSWERS:")
        print("="*80)
        
        answers = data.get('answers', {})
        print(f"\nTotal answers saved: {len(answers)}")
        
        for idx_str, answer in sorted(answers.items(), key=lambda x: int(x[0])):
            idx = int(idx_str)
            if idx < len(questions):
                q = questions[idx]
                q_type = q.get('type')
                title = q.get('title', '')[:50]
                
                print(f"\n[{idx}] {q_type}: {title}...")
                print(f"      Answer: {answer}")
                
                if q_type == 'linear_scale' and not answer:
                    print(f"      ⚠️  Linear scale but NO ANSWER!")
        
        return data
        
    except FileNotFoundError:
        print(f"❌ File {json_file} không tồn tại!")
        print("   Hãy extract form trước bằng tool")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_extracted_questions()
