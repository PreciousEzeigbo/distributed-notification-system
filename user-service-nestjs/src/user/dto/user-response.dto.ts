import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class UserResponseDto {
  @ApiProperty({
    description: 'User unique identifier',
    example: '123e4567-e89b-12d3-a456-426614174000',
    format: 'uuid'
  })
  id: string;

  @ApiProperty({
    description: 'User email address',
    example: 'user@example.com'
  })
  email: string;

  @ApiPropertyOptional({
    description: 'User password (hashed)',
    example: '$2b$10$...',
    nullable: true
  })
  password?: string | null;

  @ApiPropertyOptional({
    description: 'Firebase Cloud Messaging push token',
    example: 'fcm_token_abc123xyz',
    nullable: true
  })
  push_token?: string | null;

  @ApiProperty({
    description: 'User notification preferences',
    example: { email: true, push: true }
  })
  preferences: {
    email: boolean;
    push: boolean;
  };
}

export class ApiResponseDto<T = any> {
  @ApiProperty({
    description: 'Indicates if the operation was successful',
    example: true
  })
  success: boolean;

  @ApiProperty({
    description: 'Human-readable message about the operation',
    example: 'User retrieved successfully'
  })
  message: string;

  @ApiPropertyOptional({
    description: 'Response data payload',
    nullable: true
  })
  data?: T | null;

  @ApiPropertyOptional({
    description: 'Error message if operation failed',
    nullable: true,
    example: null
  })
  error?: string | null;

  @ApiPropertyOptional({
    description: 'Pagination metadata',
    nullable: true,
    example: null
  })
  meta?: any | null;
}

export class UpdatePreferencesDto {
  @ApiPropertyOptional({
    description: 'Enable/disable email notifications',
    example: true
  })
  email?: boolean;

  @ApiPropertyOptional({
    description: 'Enable/disable push notifications',
    example: true
  })
  push?: boolean;
}

export class UpdatePushTokenDto {
  @ApiProperty({
    description: 'Firebase Cloud Messaging push token',
    example: 'fcm_token_abc123xyz'
  })
  push_token: string;
}
