import { Module } from '@nestjs/common';
import { TemplatesController } from './templates.controller';
import { TemplatesService } from './templates.service';
import { RabbitMQService } from '../rabbitmq/rabbitmq.service';

@Module({
  controllers: [TemplatesController],
  providers: [TemplatesService, RabbitMQService],
})
export class TemplatesModule {}
