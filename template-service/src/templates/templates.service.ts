import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { RabbitMQService } from '../rabbitmq/rabbitmq.service';

@Injectable()
export class TemplatesService {
  private prisma = new PrismaClient();

  constructor(private readonly rabbitMQ: RabbitMQService) {}

  async createTemplate(data: any) {
    const template = await this.prisma.template.create({ data });
    await this.rabbitMQ.publish('template.created', template);
    return template;
  }

  async getTemplates() {
    return this.prisma.template.findMany();
  }

  async getTemplateById(id: string) {
    return this.prisma.template.findUnique({ where: { id } });
  }

  async updateTemplate(id: string, data: any) {
    return this.prisma.template.update({ where: { id }, data });
  }

  async deleteTemplate(id: string) {
    return this.prisma.template.delete({ where: { id } });
  }
}
