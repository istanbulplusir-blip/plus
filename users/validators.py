"""
Custom validators for user registration and authentication
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class EmailValidator:
    """Enhanced email validator with additional security checks"""
    
    # Blocked email domains and patterns
    BLOCKED_DOMAINS = {
        'test.com', 'example.com', 'localhost', '127.0.0.1', '0.0.0.0',
        'temp-mail.org', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'tempmail.org',
        'test', 'fawf', 'fake', 'dummy', 'sample', 'temp', 'temporary',
        'admin.test', 'test.admin', 'admin@test', 'test@admin'
    }
    
    # Blocked email patterns
    BLOCKED_PATTERNS = [
        r'.*@test\..*',
        r'.*@example\..*',
        r'.*@localhost.*',
        r'.*@temp.*',
        r'.*@fake.*',
        r'.*@dummy.*',
        r'.*@sample.*',
        r'.*@fawf\..*',
        r'.*@temporary\..*',
        r'^test.*@.*',
        r'^fake.*@.*',
        r'^dummy.*@.*',
        r'^sample.*@.*',
        r'^admin.*@.*',
        r'^user.*@.*',
        r'^guest.*@.*',
        r'^temp.*@.*',
        r'^fawf.*@.*',
        r'.*@.*\.test$',
        r'.*@.*\.fake$',
        r'.*@.*\.dummy$',
        r'.*@.*\.fawf$',
        r'.*@.*\.temp$',
        r'.*@.*\.temporary$',
        r'^admin@test\.com$',
        r'^test@admin\.com$',
        r'^admin@test$',
        r'^test@admin$'
    ]
    
    @classmethod
    def validate_email(cls, email):
        """Validate email with enhanced security checks"""
        if not email:
            raise ValidationError("ایمیل الزامی است")
        
        email = email.strip().lower()
        
        # Basic Django email validation
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("فرمت ایمیل نامعتبر است")
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Check blocked domains
        if domain in cls.BLOCKED_DOMAINS:
            raise ValidationError("این دامنه ایمیل مجاز نیست")
        
        # Check blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.match(pattern, email, re.IGNORECASE):
                raise ValidationError("این نوع ایمیل مجاز نیست")
        
        # Check for suspicious patterns
        if cls._is_suspicious_email(email):
            raise ValidationError("ایمیل وارد شده مشکوک است")
        
        return email
    
    @classmethod
    def _is_suspicious_email(cls, email):
        """Check for suspicious email patterns"""
        suspicious_patterns = [
            r'.*\d{6,}.*@.*',  # Too many numbers (6 or more)
            r'.*[!@#$%^&*()+=\[\]{}|;:,<>?].*@.*',  # Special chars in local part (excluding dots and underscores)
            r'.*\.{2,}.*',  # Multiple consecutive dots
            r'^.{1,2}@.*',  # Too short local part
            r'.*@.{1,2}$',  # Too short domain
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, email):
                return True
        
        return False


class PhoneValidator:
    """Enhanced phone number validator for Iranian mobile numbers"""
    
    # Valid Iranian mobile prefixes
    VALID_PREFIXES = {
        '0910', '0911', '0912', '0913', '0914', '0915', '0916', '0917', '0918', '0919',
        '0990', '0991', '0992', '0993', '0994', '0995', '0996', '0997', '0998', '0999',
        '0901', '0902', '0903', '0905', '0930', '0931', '0932', '0933', '0934', '0935',
        '0936', '0937', '0938', '0939', '0940', '0941', '0942', '0943', '0944', '0945',
        '0946', '0947', '0948', '0949', '0950', '0951', '0952', '0953', '0954', '0955',
        '0956', '0957', '0958', '0959', '0960', '0961', '0962', '0963', '0964', '0965',
        '0966', '0967', '0968', '0969', '0970', '0971', '0972', '0973', '0974', '0975',
        '0976', '0977', '0978', '0979', '0980', '0981', '0982', '0983', '0984', '0985',
        '0986', '0987', '0988', '0989'
    }
    
    # Blocked/test phone patterns
    BLOCKED_PATTERNS = [
        r'^\+989000000000$',
        r'^\+989111111111$',
        r'^\+989222222222$',
        r'^\+989333333333$',
        r'^\+989444444444$',
        r'^\+989555555555$',
        r'^\+989666666666$',
        r'^\+989777777777$',
        r'^\+989888888888$',
        r'^\+989999999999$',
        r'^\+989123456789$',
        r'^\+989876543210$',
        r'^09123456789$',
        r'^09876543210$',
        r'^09111111111$',
        r'^09222222222$',
        r'^09333333333$',
        r'^09444444444$',
        r'^09555555555$',
        r'^09666666666$',
        r'^09777777777$',
        r'^09888888888$',
        r'^09999999999$'
    ]
    
    @classmethod
    def validate_phone(cls, phone):
        """Validate Iranian mobile phone number"""
        if not phone:
            raise ValidationError("شماره موبایل الزامی است")
        
        phone = phone.strip()
        
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', phone)
        
        # Check blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.match(pattern, phone):
                raise ValidationError("این شماره موبایل مجاز نیست")
        
        # Handle different formats
        if phone.startswith('+98'):
            # International format: +989123456789
            if len(phone) != 13:
                raise ValidationError("فرمت شماره موبایل نامعتبر است")
            local_phone = '0' + phone[3:]
        elif phone.startswith('09'):
            # Local format: 09123456789
            if len(phone) != 11:
                raise ValidationError("فرمت شماره موبایل نامعتبر است")
            local_phone = phone
        else:
            raise ValidationError("شماره موبایل باید با 09 یا +98 شروع شود")
        
        # Check if it's a valid Iranian mobile prefix
        prefix = local_phone[:4]
        if prefix not in cls.VALID_PREFIXES:
            raise ValidationError("پیش‌شماره موبایل نامعتبر است")
        
        # Check for suspicious patterns
        if cls._is_suspicious_phone(phone):
            raise ValidationError("شماره موبایل وارد شده مشکوک است")
        
        # Return in international format
        return '+98' + local_phone[1:]
    
    @classmethod
    def _is_suspicious_phone(cls, phone):
        """Check for suspicious phone patterns"""
        # Remove +98 prefix for checking
        local_phone = phone[3:] if phone.startswith('+98') else phone
        
        # Check for repeated digits (more than 4 consecutive)
        if re.search(r'(\d)\1{4,}', local_phone):
            return True
        
        # Check for sequential digits
        if re.search(r'(0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|3210)', local_phone):
            return True
        
        # Check for too many zeros
        if local_phone.count('0') > 6:
            return True
        
        return False


class ContactInfoValidator:
    """Validator for contact info (email or phone) in registration"""
    
    @classmethod
    def validate_contact_info(cls, value):
        """Validate contact info and detect type"""
        if not value:
            raise ValidationError("اطلاعات تماس الزامی است")
        
        value = value.strip()
        
        # Try to validate as email first
        if '@' in value:
            try:
                email = EmailValidator.validate_email(value)
                return {
                    'value': email,
                    'type': 'email',
                    'delivery_method': 'email'
                }
            except ValidationError as e:
                raise ValidationError(str(e))
        
        # Try to validate as phone
        try:
            phone = PhoneValidator.validate_phone(value)
            return {
                'value': phone,
                'type': 'phone',
                'delivery_method': 'sms'
            }
        except ValidationError as e:
            raise ValidationError(str(e))
        
        # If neither email nor phone, raise error
        raise ValidationError("لطفاً ایمیل معتبر یا شماره موبایل وارد کنید")


def validate_username(username):
    """Enhanced username validator"""
    if not username:
        raise ValidationError("نام کاربری الزامی است")
    
    username = username.strip()
    
    # Length check
    if len(username) < 3:
        raise ValidationError("نام کاربری باید حداقل 3 کاراکتر باشد")
    
    if len(username) > 30:
        raise ValidationError("نام کاربری نباید بیشتر از 30 کاراکتر باشد")
    
    # Character check (only letters, numbers, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError("نام کاربری فقط می‌تواند شامل حروف، اعداد، خط تیره و زیرخط باشد")
    
    # Cannot start or end with special characters
    if username.startswith(('_', '-')) or username.endswith(('_', '-')):
        raise ValidationError("نام کاربری نمی‌تواند با خط تیره یا زیرخط شروع یا تمام شود")
    
    # Cannot be all numbers
    if username.isdigit():
        raise ValidationError("نام کاربری نمی‌تواند فقط شامل اعداد باشد")
    
    # Blocked usernames
    blocked_usernames = {
        'admin', 'administrator', 'root', 'user', 'test', 'guest', 'anonymous',
        'api', 'www', 'mail', 'email', 'support', 'help', 'info', 'contact',
        'about', 'privacy', 'terms', 'login', 'register', 'signup', 'signin',
        'dashboard', 'profile', 'account', 'settings', 'config', 'system',
        'null', 'undefined', 'true', 'false', 'yes', 'no', 'ok', 'error',
        'fawf', 'fake', 'dummy', 'sample', 'temp', 'temporary', 'demo',
        'tester', 'testing', 'testuser', 'testuser1', 'testuser2', 'testuser3',
        'admin1', 'admin2', 'admin3', 'user1', 'user2', 'user3', 'guest1',
        'guest2', 'guest3', 'demo1', 'demo2', 'demo3', 'sample1', 'sample2',
        'sample3', 'fake1', 'fake2', 'fake3', 'dummy1', 'dummy2', 'dummy3'
    }
    
    if username.lower() in blocked_usernames:
        raise ValidationError("این نام کاربری مجاز نیست")
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'^test\d+$',  # test1, test2, etc.
        r'^admin\d+$',  # admin1, admin2, etc.
        r'^user\d+$',   # user1, user2, etc.
        r'^guest\d+$',  # guest1, guest2, etc.
        r'^demo\d+$',   # demo1, demo2, etc.
        r'^fake\d+$',   # fake1, fake2, etc.
        r'^dummy\d+$',  # dummy1, dummy2, etc.
        r'^sample\d+$', # sample1, sample2, etc.
        r'^temp\d+$',   # temp1, temp2, etc.
        r'^fawf\d+$',   # fawf1, fawf2, etc.
        r'.*test.*',    # anything containing 'test'
        r'.*admin.*',   # anything containing 'admin'
        r'.*fake.*',    # anything containing 'fake'
        r'.*dummy.*',   # anything containing 'dummy'
        r'.*sample.*',  # anything containing 'sample'
        r'.*temp.*',    # anything containing 'temp'
        r'.*fawf.*',    # anything containing 'fawf'
    ]
    
    for pattern in suspicious_patterns:
        if re.match(pattern, username.lower()):
            raise ValidationError("این نام کاربری مجاز نیست")
    
    return username
