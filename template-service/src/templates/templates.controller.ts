import { Body, Controller, Get, Param, Post, Put, Delete } from '@nestjs/common';
import { TemplatesService } from './templates.service';

@Controller('templates')
export class TemplatesController {
  constructor(private readonly templatesService: TemplatesService) {}

  @Post()
  async create(@Body() body: any) {
    return this.templatesService.createTemplate(body);
  }

  @Get()
  async findAll() {
    return this.templatesService.getTemplates();
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.templatesService.getTemplateById(id);
  }

  @Put(':id')
  async update(@Param('id') id: string, @Body() body: any) {
    return this.templatesService.updateTemplate(id, body);
  }

  @Delete(':id')
  async remove(@Param('id') id: string) {
    return this.templatesService.deleteTemplate(id);
  }
}
