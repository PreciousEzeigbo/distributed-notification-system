import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsIn, IsOptional, IsInt } from 'class-validator';

export class UpdateTemplateDto {
  @ApiPropertyOptional({
    description: 'Template code identifier',
    example: 'WELCOME_EMAIL_V2'
  })
  @IsString()
  @IsOptional()
  code?: string;

  @ApiPropertyOptional({
    description: 'Human-readable template name',
    example: 'Updated Welcome Email'
  })
  @IsString()
  @IsOptional()
  name?: string;

  @ApiPropertyOptional({
    description: 'Email subject line',
    example: 'Welcome aboard, {{name}}!'
  })
  @IsString()
  @IsOptional()
  subject?: string;

  @ApiPropertyOptional({
    description: 'Template body with variable placeholders',
    example: 'Hello {{name}}, welcome to our platform!'
  })
  @IsString()
  @IsOptional()
  body?: string;

  @ApiPropertyOptional({
    description: 'Template type (email or push)',
    example: 'email',
    enum: ['email', 'push']
  })
  @IsString()
  @IsIn(['email', 'push'])
  @IsOptional()
  type?: string;

  @ApiPropertyOptional({
    description: 'Template language code',
    example: 'en'
  })
  @IsString()
  @IsOptional()
  language?: string;

  @ApiPropertyOptional({
    description: 'Template version number',
    example: 2
  })
  @IsInt()
  @IsOptional()
  version?: number;
}
