import { Controller, Get, Post, Put, Delete, Body, Param, UseInterceptors } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam, ApiBody } from '@nestjs/swagger';
import { TemplateService } from './template.service';
import { Template } from './template.entity';
import {
  CreateTemplateDto,
  UpdateTemplateDto,
  TemplateResponseDto,
  ApiResponseDto,
  RenderTemplateDto,
  RenderTemplateResponseDto
} from './dto';
import { ResponseInterceptor } from '../common/interceptors/response.interceptor';

@ApiTags('templates')
@Controller('templates')
@UseInterceptors(ResponseInterceptor)
export class TemplateController {
  constructor(private readonly templateService: TemplateService) {}

  @Post()
  @ApiOperation({ summary: 'Create new template' })
  @ApiBody({ type: CreateTemplateDto })
  @ApiResponse({
    status: 201,
    description: 'Template created successfully',
    type: ApiResponseDto<TemplateResponseDto>
  })
  async create(@Body() templateData: CreateTemplateDto): Promise<Template> {
    return this.templateService.create(templateData);
  }

  @Get()
  @ApiOperation({ summary: 'Get all templates' })
  @ApiResponse({
    status: 200,
    description: 'Return all templates',
    type: ApiResponseDto<TemplateResponseDto[]>
  })
  async findAll(): Promise<Template[]> {
    return this.templateService.findAll();
  }

  @Get('code/:code')
  @ApiOperation({ summary: 'Get template by code' })
  @ApiParam({ name: 'code', type: 'string', description: 'Template code' })
  @ApiResponse({
    status: 200,
    description: 'Return template by code',
    type: ApiResponseDto<TemplateResponseDto>
  })
  async findByCode(@Param('code') code: string): Promise<Template> {
    return this.templateService.findByCode(code);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get template by ID' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'Template UUID' })
  @ApiResponse({
    status: 200,
    description: 'Return template',
    type: ApiResponseDto<TemplateResponseDto>
  })
  async findOne(@Param('id') id: string): Promise<Template> {
    return this.templateService.findOne(id);
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update template' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'Template UUID' })
  @ApiBody({ type: UpdateTemplateDto })
  @ApiResponse({
    status: 200,
    description: 'Template updated successfully',
    type: ApiResponseDto<TemplateResponseDto>
  })
  async update(
    @Param('id') id: string,
    @Body() templateData: UpdateTemplateDto,
  ): Promise<Template> {
    return this.templateService.update(id, templateData);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete template' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'Template UUID' })
  @ApiResponse({
    status: 200,
    description: 'Template deleted successfully',
    schema: {
      type: 'object',
      properties: {
        success: { type: 'boolean', example: true },
        message: { type: 'string', example: 'Resource deleted successfully' },
        data: { type: 'null' },
        error: { type: 'null' },
        meta: { type: 'null' }
      }
    }
  })
  async remove(@Param('id') id: string): Promise<void> {
    return this.templateService.remove(id);
  }

  @Post('render')
  @ApiOperation({ summary: 'Render template with variables' })
  @ApiBody({ type: RenderTemplateDto })
  @ApiResponse({
    status: 200,
    description: 'Template rendered successfully',
    type: RenderTemplateResponseDto
  })
  async render(
    @Body() renderData: RenderTemplateDto
  ): Promise<{ data: { subject: string; body: string } }> {
    const template = await this.templateService.findByCode(renderData.template_name);
    
    // Simple variable replacement in subject and body
    let subject = template.subject;
    let body = template.body;
    
    for (const [key, value] of Object.entries(renderData.variables)) {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      subject = subject.replace(regex, String(value));
      body = body.replace(regex, String(value));
    }
    
    return {
      data: {
        subject,
        body
      }
    };
  }
}
