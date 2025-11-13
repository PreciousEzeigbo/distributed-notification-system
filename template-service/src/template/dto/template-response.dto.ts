import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class TemplateResponseDto {
  @ApiProperty({
    description: 'Template unique identifier',
    example: '123e4567-e89b-12d3-a456-426614174000',
    format: 'uuid'
  })
  id: string;

  @ApiProperty({
    description: 'Unique template code identifier',
    example: 'WELCOME_EMAIL'
  })
  code: string;

  @ApiProperty({
    description: 'Human-readable template name',
    example: 'Welcome Email Template'
  })
  name: string;

  @ApiProperty({
    description: 'Email subject line',
    example: 'Welcome to our platform, {{name}}!'
  })
  subject: string;

  @ApiProperty({
    description: 'Template body with variable placeholders',
    example: 'Hi {{name}}, welcome!'
  })
  body: string;

  @ApiProperty({
    description: 'Template type (email or push)',
    example: 'email'
  })
  type: string;

  @ApiProperty({
    description: 'Template language code',
    example: 'en'
  })
  language: string;

  @ApiProperty({
    description: 'Template version number',
    example: 1
  })
  version: number;

  @ApiProperty({
    description: 'Template creation timestamp',
    example: '2025-11-13T08:00:00.000Z'
  })
  created_at: Date;

  @ApiProperty({
    description: 'Template last update timestamp',
    example: '2025-11-13T08:00:00.000Z'
  })
  updated_at: Date;
}

export class ApiResponseDto<T = any> {
  @ApiProperty({
    description: 'Indicates if the operation was successful',
    example: true
  })
  success: boolean;

  @ApiProperty({
    description: 'Human-readable message about the operation',
    example: 'Template retrieved successfully'
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

export class RenderTemplateDto {
  @ApiProperty({
    description: 'Template code to render',
    example: 'WELCOME_EMAIL'
  })
  template_name: string;

  @ApiProperty({
    description: 'Variables to substitute in template',
    example: { name: 'John Doe', email: 'john@example.com' }
  })
  variables: Record<string, any>;

  @ApiPropertyOptional({
    description: 'Language code for template',
    example: 'en',
    default: 'en'
  })
  language?: string;
}

export class RenderTemplateResponseDto {
  @ApiProperty({
    description: 'Rendered template data',
    type: 'object',
    properties: {
      subject: { type: 'string', example: 'Welcome to our platform, John Doe!' },
      body: { type: 'string', example: 'Hi John Doe, welcome! Your email is john@example.com.' }
    }
  })
  data: {
    subject: string;
    body: string;
  };
}
