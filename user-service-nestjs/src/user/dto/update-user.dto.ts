import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsEmail, IsString, IsOptional, IsObject } from 'class-validator';
import { PreferencesDto } from './create-user.dto';

export class UpdateUserDto {
  @ApiPropertyOptional({
    description: 'User email address',
    example: 'newemail@example.com'
  })
  @IsEmail()
  @IsOptional()
  email?: string;

  @ApiPropertyOptional({
    description: 'User password',
    example: 'newSecurePassword123'
  })
  @IsString()
  @IsOptional()
  password?: string;

  @ApiPropertyOptional({
    description: 'Firebase Cloud Messaging push token',
    example: 'fcm_token_new123'
  })
  @IsString()
  @IsOptional()
  push_token?: string;

  @ApiPropertyOptional({
    description: 'User notification preferences',
    type: PreferencesDto
  })
  @IsObject()
  @IsOptional()
  preferences?: PreferencesDto;
}
