import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsIn, IsOptional, IsInt } from 'class-validator';

export class CreateTemplateDto {
  @ApiProperty({
    description: 'Unique template code identifier',
    example: 'WELCOME_EMAIL'
  })
  @IsString()
  code: string;

  @ApiProperty({
    description: 'Human-readable template name',
    example: 'Welcome Email Template'
  })
  @IsString()
  name: string;

  @ApiProperty({
    description: 'Email subject line',
    example: 'Welcome to our platform, {{name}}!'
  })
  @IsString()
  subject: string;

  @ApiProperty({
    description: 'Template body with variable placeholders',
    example: 'Hi {{name}}, welcome! Your email is {{email}}.'
  })
  @IsString()
  body: string;

  @ApiProperty({
    description: 'Template type (email or push)',
    example: 'email',
    enum: ['email', 'push']
  })
  @IsString()
  @IsIn(['email', 'push'])
  type: string;

  @ApiPropertyOptional({
    description: 'Template language code',
    example: 'en',
    default: 'en'
  })
  @IsString()
  @IsOptional()
  language?: string;

  @ApiPropertyOptional({
    description: 'Template version number',
    example: 1,
    default: 1
  })
  @IsInt()
  @IsOptional()
  version?: number;
}
