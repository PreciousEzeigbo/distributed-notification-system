import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsEmail, IsString, IsOptional, IsObject } from 'class-validator';

export class PreferencesDto {
  @ApiProperty({ 
    description: 'Enable email notifications',
    example: true,
    default: true
  })
  email: boolean;

  @ApiProperty({ 
    description: 'Enable push notifications',
    example: true,
    default: true
  })
  push: boolean;
}

export class CreateUserDto {
  @ApiProperty({
    description: 'User email address',
    example: 'user@example.com'
  })
  @IsEmail()
  email: string;

  @ApiPropertyOptional({
    description: 'User password',
    example: 'securePassword123'
  })
  @IsString()
  @IsOptional()
  password?: string;

  @ApiPropertyOptional({
    description: 'Firebase Cloud Messaging push token',
    example: 'fcm_token_abc123xyz'
  })
  @IsString()
  @IsOptional()
  push_token?: string;

  @ApiPropertyOptional({
    description: 'User notification preferences',
    type: PreferencesDto,
    default: { email: true, push: true }
  })
  @IsObject()
  @IsOptional()
  preferences?: PreferencesDto;
}
