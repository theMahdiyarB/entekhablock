"""
Script to initialize ENTEKHABLOCK system
Handles voter database creation and polling file initialization
"""

import os
import sys
import json
from datetime import datetime

def create_database():
    """Create initial data structures"""
    try:
        os.makedirs('data', exist_ok=True)
        
        # Initialize voters CSV if it doesn't exist
        voters_path = 'data/voters.csv'
        if not os.path.exists(voters_path):
            with open(voters_path, 'w', encoding='utf-8') as f:
                f.write('national_code,birth_date,serial_number,mobile,full_name\n')
            print("✅ Voters database created at data/voters.csv")
        else:
            print("ℹ️  Voters database already exists")
        
        # Initialize polls file if it doesn't exist
        polls_path = 'data/polls.json'
        if not os.path.exists(polls_path):
            with open(polls_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("✅ Polls file created at data/polls.json")
        else:
            print("ℹ️  Polls file already exists")
        
        # Initialize blockchain file if it doesn't exist
        blockchain_path = 'data/blockchain.json'
        if not os.path.exists(blockchain_path):
            with open(blockchain_path, 'w', encoding='utf-8') as f:
                json.dump({"chain": []}, f, ensure_ascii=False, indent=2)
            print("✅ Blockchain file created at data/blockchain.json")
        else:
            print("ℹ️  Blockchain file already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        return False



def load_sample_voters():
    """Load sample voter data"""
    try:
        voters_path = 'data/voters.csv'
        
        # Check if voters already exist
        with open(voters_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                print(f"ℹ️  Voters already exist ({len(lines)-1} entries)")
                return True
        
        # Add sample voters
        sample_voters = [
            "1234567890,1995-05-15,123456,09101234567,علی احمدی",
            "0987654321,1990-03-22,654321,09109876543,فاطمه موسوی",
            "1111111111,1992-07-10,111111,09111111111,محمد رضایی"
        ]
        
        with open(voters_path, 'a', encoding='utf-8') as f:
            for voter in sample_voters:
                f.write(voter + '\n')
        
        print(f"✅ Loaded {len(sample_voters)} sample voters")
        return True
        
    except Exception as e:
        print(f"❌ Error loading sample voters: {str(e)}")
        return False


def show_database_info():
    """Show database statistics"""
    try:
        print("\n" + "="*50)
        print("📊 سیستم آماری ENTEKHABLOCK")
        print("="*50)
        
        # Check voters
        voters_path = 'data/voters.csv'
        if os.path.exists(voters_path):
            with open(voters_path, 'r', encoding='utf-8') as f:
                voter_count = len(f.readlines()) - 1
            print(f"👥 Registered voters: {voter_count}")
        
        # Check polls
        polls_path = 'data/polls.json'
        if os.path.exists(polls_path):
            with open(polls_path, 'r', encoding='utf-8') as f:
                polls = json.load(f)
            print(f"📋 Active polls: {len(polls)}")
        
        # Check blockchain
        blockchain_path = 'data/blockchain.json'
        if os.path.exists(blockchain_path):
            with open(blockchain_path, 'r', encoding='utf-8') as f:
                blockchain = json.load(f)
            print(f"⛓️  Blockchain blocks: {len(blockchain.get('chain', []))}")
        
        print("="*50 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Error reading database info: {str(e)}")
        return False


def run_setup():
    """Run complete system setup"""
    print("\n🚀 شروع راه‌اندازی اولیه سیستم...\n")
    
    if not create_database():
        return False
    
    if not load_sample_voters():
        return False
    
    show_database_info()
    
    print("✨ راه‌اندازی با موفقیت انجام شد!")
    print("\n💡 نکات مهم:")
    print("   - می‌توانید با دستور 'python app.py' برنامه را اجرا کنید")
    print("   - برای ورود به پنل ادمین از اطلاعات زیر استفاده کنید:")
    print("   - نام کاربری: admin")
    print("   - رمز عبور: admin")
    print("   - کد OTP: 1234")
    print("="*50 + "\n")
    
    return True


if __name__ == '__main__':
    # Show header
    print("="*50)
    print("🗳️  سیستم مدیریت ENTEKHABLOCK")
    print("="*50)
    print(f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Auto setup mode
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        run_setup()
    else:
        # Interactive menu
        while True:
            print("\n🔧 مدیریت سیستم")
            print("="*50)
            print("1. ایجاد دیتابیس و فایل‌ها")
            print("2. بارگذاری نمونه رأی‌دهندگان")
            print("3. نمایش آمار دیتابیس")
            print("4. راه‌اندازی کامل (گزینه‌های 1 و 2)")
            print("0. خروج")
            print("="*50)
            
            choice = input("\nگزینه مورد نظر را انتخاب کنید: ")
            
            if choice == '1':
                create_database()
            elif choice == '2':
                load_sample_voters()
            elif choice == '3':
                show_database_info()
            elif choice == '4':
                run_setup()
            elif choice == '0':
                print("\n👋 خروج از برنامه...")
                break
            else:
                print("\n❌ گزینه نامعتبر!")
            
            if choice != '0':
                input("\nبرای ادامه Enter را فشار دهید...")
            elif choice == '3':
                show_database_info()
            elif choice == '4':
                reset_admin_password()
            elif choice == '5':
                clear_votes()
            elif choice == '6':
                run_setup()
            elif choice == '0':
                print("\n👋 خروج از برنامه...")
                break
            else:
                print("\n❌ گزینه نامعتبر! لطفاً دوباره تلاش کنید.")
            
            input("\nبرای ادامه Enter را فشار دهید...")
