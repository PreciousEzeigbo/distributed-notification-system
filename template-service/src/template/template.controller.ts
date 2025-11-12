import { Controller, Get, Post, Put, Delete, Body, Param } from '@nestjs/common';
import { TemplateService } from './template.service';
import { Template } from './template.entity';

@Controller('templates')
export class TemplateController {
  constructor(private readonly templateService: TemplateService) {}

  @Post()
  async create(@Body() templateData: Partial<Template>): Promise<Template> {
    return this.templateService.create(templateData);
  }

  @Get()
  async findAll(): Promise<Template[]> {
    return this.templateService.findAll();
  }

  @Get('code/:code')
  async findByCode(@Param('code') code: string): Promise<Template> {
    return this.templateService.findByCode(code);
  }

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<Template> {
    return this.templateService.findOne(id);
  }

  @Put(':id')
  async update(
    @Param('id') id: string,
    @Body() templateData: Partial<Template>,
  ): Promise<Template> {
    return this.templateService.update(id, templateData);
  }

  @Delete(':id')
  async remove(@Param('id') id: string): Promise<void> {
    return this.templateService.remove(id);
  }
}
