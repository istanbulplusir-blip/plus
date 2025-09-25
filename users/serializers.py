from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User
from .services.otp import OTPService, verify_otp
from .validators import ContactInfoValidator, EmailValidator, PhoneValidator, validate_username


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone_otp_code = serializers.CharField(write_only=True, required=False, help_text="OTP code for phone verification")
    send_email_verification = serializers.BooleanField(default=True, help_text="Send email verification after registration")

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password', 'password_confirm', 'phone_otp_code', 'send_email_verification')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        # If phone is provided, OTP verification is required
        if data.get('phone') and not data.get('phone_otp_code'):
            raise serializers.ValidationError("Phone OTP verification is required when providing phone number")
        
        # Verify phone OTP if provided
        if data.get('phone') and data.get('phone_otp_code'):
            success, message, otp_obj = OTPService.verify_otp(
                contact_info=data['phone'],
                code=data['phone_otp_code'],
                purpose='register'
            )
            if not success:
                raise serializers.ValidationError(f"Phone OTP verification failed: {message}")
        
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        phone_otp_code = validated_data.pop('phone_otp_code', None)
        send_email_verification = validated_data.pop('send_email_verification', True)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # If phone was verified during registration, mark it as verified
        if user.phone and phone_otp_code:
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
        
        # Send email verification if requested
        if send_email_verification and user.email:
            from users.services.verification import VerificationService
            try:
                VerificationService.send_email_verification(user, user.email)
            except Exception as e:
                # Don't fail registration if email sending fails
                pass
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    otp_code = serializers.CharField(required=False, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        otp_code = data.get('otp_code')

        if otp_code:
            # OTP login - try to find user by username, email, or phone
            user = None
            if '@' in username:
                # Try email
                user = User.objects.filter(email=username).first()
            elif username.startswith('+'):
                # Try phone
                user = User.objects.filter(phone=username).first()
            else:
                # Try username
                user = User.objects.filter(username=username).first()
            
            if not user:
                raise serializers.ValidationError("User not found")
            # For OTP login, we need either phone or email
            if not user.phone and not user.email:
                raise serializers.ValidationError("No phone number or email registered for this user")
            if not user.is_active:
                raise serializers.ValidationError("User account is deactivated")
            if user.is_locked():
                raise serializers.ValidationError("User account is temporarily locked")
            # Use phone if available, otherwise use email
            contact_info = user.phone if user.phone else user.email
            delivery_method = 'sms' if user.phone else 'email'
            success, message, otp_obj = OTPService.verify_otp(
                contact_info=contact_info,
                code=otp_code,
                purpose='login'
            )
            if not success:
                raise serializers.ValidationError(f"Invalid or expired OTP code: {message}")
        else:
            # Password login - try to find user by username, email, or phone
            user = None
            if '@' in username:
                # Try email
                user = User.objects.filter(email=username).first()
                if user and user.check_password(password):
                    pass  # User found and password matches
                else:
                    user = None
            elif username.startswith('+'):
                # Try phone
                user = User.objects.filter(phone=username).first()
                if user and user.check_password(password):
                    pass  # User found and password matches
                else:
                    user = None
            else:
                # Try username
                user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is deactivated")
            if user.is_locked():
                raise serializers.ValidationError("User account is temporarily locked")
        data['user'] = user
        return data


class SendOtpSerializer(serializers.Serializer):
    # Support both phone and email for backward compatibility
    phone = serializers.CharField(required=False, help_text="Phone number (for backward compatibility)")
    contact_info = serializers.CharField(required=False, help_text="Email address or phone number")
    delivery_method = serializers.ChoiceField(
        choices=['sms', 'email'], 
        default='sms',
        help_text="Delivery method for OTP"
    )
    purpose = serializers.ChoiceField(
        choices=['login', 'register', 'password_reset', 'email_verify', 'phone_verify'], 
        default='login'
    )

    def validate(self, data):
        # Ensure either phone or contact_info is provided
        if not data.get('contact_info') and not data.get('phone'):
            raise serializers.ValidationError("Either contact_info or phone must be provided")
        
        # If phone is provided but not contact_info, use phone as contact_info
        if data.get('phone') and not data.get('contact_info'):
            data['contact_info'] = data['phone']
            data['delivery_method'] = 'sms'
        
        # Validate contact_info format based on delivery method
        contact_info = data.get('contact_info')
        delivery_method = data.get('delivery_method', 'sms')
        
        if delivery_method == 'email':
            try:
                EmailValidator.validate_email(contact_info)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        elif delivery_method == 'sms':
            try:
                PhoneValidator.validate_phone(contact_info)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        
        return data


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()
    purpose = serializers.ChoiceField(choices=['login', 'register'], default='login')

    def validate(self, data):
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=data['phone'],
            code=data['code'],
            purpose=data['purpose']
        )
        if not success:
            raise serializers.ValidationError(f"Invalid or expired OTP code: {message}")
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'avatar', 'avatar_url', 'birth_date', 'email_verified', 'phone_verified',
            'two_factor_enabled', 'email_notifications', 'sms_notifications'
        )
        read_only_fields = ('id', 'email_verified', 'phone_verified', 'avatar_url')
        extra_kwargs = {
            'avatar': {'write_only': True},
            'birth_date': {'required': False},
            'email_notifications': {'required': False},
            'sms_notifications': {'required': False},
        }
    
    def get_avatar_url(self, obj):
        """Get avatar URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def validate_email(self, value):
        """Validate email with enhanced security and uniqueness"""
        if value:
            try:
                validated_email = EmailValidator.validate_email(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
            
            # Check uniqueness
            user = self.instance
            if user and User.objects.filter(email=validated_email).exclude(id=user.id).exists():
                raise serializers.ValidationError("این ایمیل قبلاً استفاده شده است.")
            
            return validated_email
        return value
    
    def validate_phone(self, value):
        """Validate phone with enhanced security and uniqueness"""
        if value:
            try:
                validated_phone = PhoneValidator.validate_phone(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
            
            # Check uniqueness
            user = self.instance
            if user and User.objects.filter(phone=validated_phone).exclude(id=user.id).exists():
                raise serializers.ValidationError("این شماره موبایل قبلاً استفاده شده است.")
            
            return validated_phone
        return value
    
    def validate_avatar(self, value):
        """Validate avatar file"""
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("حجم فایل نباید بیشتر از 5 مگابایت باشد.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError("فرمت فایل باید JPEG، PNG، GIF یا WebP باشد.")
        
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    contact_info = serializers.CharField(
        help_text="Email address or phone number"
    )
    delivery_method = serializers.ChoiceField(
        choices=['email', 'sms'],
        default='email',
        help_text="Method to receive reset code"
    )

    def validate_contact_info(self, value):
        """Validate that contact info belongs to an existing user"""
        try:
            # Use enhanced validator to validate format
            contact_data = ContactInfoValidator.validate_contact_info(value)
            validated_value = contact_data['value']
            
            # Check if user exists
            if contact_data['type'] == 'email':
                user = User.objects.filter(email=validated_value).first()
                if not user:
                    raise serializers.ValidationError("کاربری با این ایمیل یافت نشد")
            else:  # phone
                user = User.objects.filter(phone=validated_value).first()
                if not user:
                    raise serializers.ValidationError("کاربری با این شماره موبایل یافت نشد")
            
            return validated_value
        except Exception as e:
            raise serializers.ValidationError(str(e))


class PasswordResetVerifySerializer(serializers.Serializer):
    """Serializer for password reset OTP verification"""
    contact_info = serializers.CharField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        """Verify OTP code"""
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=data['contact_info'],
            code=data['otp_code'],
            purpose='password_reset'
        )
        if not success:
            raise serializers.ValidationError("Invalid or expired OTP code")
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for setting new password after OTP verification"""
    contact_info = serializers.CharField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )

    def validate(self, data):
        """Validate passwords match and OTP is valid"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Verify OTP is still valid
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=data['contact_info'],
            code=data['otp_code'],
            purpose='password_reset'
        )
        if not success:
            raise serializers.ValidationError("Invalid or expired OTP code")
        
        return data

    def save(self):
        """Set new password for the user"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        contact_info = self.validated_data['contact_info']
        new_password = self.validated_data['new_password']
        
        # Find user by email or phone
        try:
            validate_email(contact_info)
            user = User.objects.get(email=contact_info)
        except DjangoValidationError:
            user = User.objects.get(phone=contact_info)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Reset failed login attempts
        user.reset_failed_attempts()
        
        return user


class SendEmailVerificationSerializer(serializers.Serializer):
    """Serializer for sending email verification link"""
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        """Validate email belongs to current user or is provided for registration"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # For authenticated users, use their email if not provided
            if not value:
                value = request.user.email
            elif value != request.user.email:
                raise serializers.ValidationError("You can only verify your own email address")
        elif not value:
            raise serializers.ValidationError("Email address is required")
        
        return value


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for verifying email with token"""
    token = serializers.CharField(max_length=64)

    def validate_token(self, value):
        """Validate verification token"""
        from users.models import EmailVerificationToken
        
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
            if not token_obj.is_valid():
                if token_obj.is_expired():
                    raise serializers.ValidationError("Verification link has expired")
                else:
                    raise serializers.ValidationError("Verification link has already been used")
            return value
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification link")


class SendPhoneVerificationSerializer(serializers.Serializer):
    """Serializer for sending phone verification OTP"""
    phone = serializers.CharField(max_length=15, required=False)

    def validate_phone(self, value):
        """Validate phone belongs to current user or is provided for registration"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # For authenticated users, use their phone if not provided
            if not value:
                if not request.user.phone:
                    raise serializers.ValidationError("No phone number associated with your account")
                value = request.user.phone
            elif value != request.user.phone:
                raise serializers.ValidationError("You can only verify your own phone number")
        elif not value:
            raise serializers.ValidationError("Phone number is required")
        
        return value


class VerifyPhoneSerializer(serializers.Serializer):
    """Serializer for verifying phone with OTP"""
    phone = serializers.CharField(max_length=15, required=False)
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        """Validate phone and OTP"""
        request = self.context.get('request')
        phone = data.get('phone')
        
        if request and request.user.is_authenticated:
            # For authenticated users, use their phone if not provided
            if not phone:
                if not request.user.phone:
                    raise serializers.ValidationError("No phone number associated with your account")
                phone = request.user.phone
                data['phone'] = phone
            elif phone != request.user.phone:
                raise serializers.ValidationError("You can only verify your own phone number")
        elif not phone:
            raise serializers.ValidationError("Phone number is required")
        
        # Verify OTP
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=phone,
            code=data['otp_code'],
            purpose='phone_verify'
        )
        if not success:
            raise serializers.ValidationError(message)
        
        return data


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification (email or phone)"""
    verification_type = serializers.ChoiceField(
        choices=['email', 'phone'],
        help_text="Type of verification to resend"
    )
    contact_info = serializers.CharField(required=False, help_text="Email or phone (optional for authenticated users)")

    def validate(self, data):
        """Validate verification type and contact info"""
        request = self.context.get('request')
        verification_type = data['verification_type']
        contact_info = data.get('contact_info')
        
        if request and request.user.is_authenticated:
            user = request.user
            if verification_type == 'email':
                if not contact_info:
                    contact_info = user.email
                elif contact_info != user.email:
                    raise serializers.ValidationError("You can only verify your own email address")
                data['contact_info'] = contact_info
            elif verification_type == 'phone':
                if not contact_info:
                    if not user.phone:
                        raise serializers.ValidationError("No phone number associated with your account")
                    contact_info = user.phone
                elif contact_info != user.phone:
                    raise serializers.ValidationError("You can only verify your own phone number")
                data['contact_info'] = contact_info
        elif not contact_info:
            raise serializers.ValidationError("Contact information is required")
        
        return data


# New Multi-Step Registration Serializers
class Step1ContactSerializer(serializers.Serializer):
    """Serializer for Step 1: Contact info validation and OTP sending"""
    contact_info = serializers.CharField(
        help_text="Email address or phone number"
    )
    
    def validate_contact_info(self, value):
        """Validate and detect contact info type with enhanced security"""
        try:
            # Use enhanced validator
            contact_data = ContactInfoValidator.validate_contact_info(value)
            
            # Store the parsed data in the serializer instance for later use
            self.contact_data = contact_data
            
            return contact_data['value']
        except ValidationError as e:
            # Re-raise ValidationError as is
            raise e
        except Exception as e:
            # Convert other exceptions to ValidationError
            raise serializers.ValidationError(str(e))


class Step1OTPVerifySerializer(serializers.Serializer):
    """Serializer for Step 1: OTP verification"""
    contact_info = serializers.CharField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, data):
        """Verify OTP and create temporary user"""
        contact_info = data['contact_info']
        otp_code = data['otp_code']
        
        # Verify OTP
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=contact_info,
            code=otp_code,
            purpose='register',
            ip_address=self.context.get('ip_address', '127.0.0.1')
        )
        
        if not success:
            raise serializers.ValidationError(message)
        
        # Check if user already exists
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        try:
            validate_email(contact_info)
            existing_user = User.objects.filter(email=contact_info).first()
        except DjangoValidationError:
            existing_user = User.objects.filter(phone=contact_info).first()
        
        if existing_user:
            raise serializers.ValidationError(
                "کاربری با این مشخصات قبلاً ثبت‌نام کرده است. لطفاً وارد شوید یا با اطلاعات دیگری ثبت‌نام کنید."
            )
        
        return data


class Step2PersonalInfoSerializer(serializers.Serializer):
    """Serializer for Step 2: Personal information"""
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    username = serializers.CharField(
        max_length=150,
        help_text="Username must be unique"
    )
    
    def validate_username(self, value):
        """Validate username with enhanced security and uniqueness"""
        # Use enhanced username validator
        try:
            validated_username = validate_username(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Check uniqueness
        if User.objects.filter(username=validated_username).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        
        return validated_username
    
    def validate_first_name(self, value):
        """Validate first name"""
        if value:
            value = value.strip()
            # Check for suspicious patterns
            if len(value) < 2:
                raise serializers.ValidationError("نام باید حداقل 2 کاراکتر باشد")
            if not value.replace(' ', '').isalpha():
                raise serializers.ValidationError("نام فقط می‌تواند شامل حروف باشد")
        return value
    
    def validate_last_name(self, value):
        """Validate last name"""
        if value:
            value = value.strip()
            # Check for suspicious patterns
            if len(value) < 2:
                raise serializers.ValidationError("نام خانوادگی باید حداقل 2 کاراکتر باشد")
            if not value.replace(' ', '').isalpha():
                raise serializers.ValidationError("نام خانوادگی فقط می‌تواند شامل حروف باشد")
        return value


class Step3PasswordSerializer(serializers.Serializer):
    """Serializer for Step 3: Password creation"""
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )
    
    def validate(self, data):
        """Validate passwords match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("رمزهای عبور مطابقت ندارند")
        return data
