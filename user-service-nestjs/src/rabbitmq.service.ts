// src/rabbitmq.service.ts
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
import { Injectable, OnModuleInit } from '@nestjs/common';
import * as amqp from 'amqplib';

@Injectable()
export class RabbitMQService implements OnModuleInit {
  private connection!: amqp.Connection;
  private channel!: amqp.Channel;

  async onModuleInit() {
    this.connection = (await amqp.connect(
      'amqp://admin:admin@rabbitmq:5672',
    )) as amqp.Connection;
    this.channel = (await this.connection.createChannel()) as amqp.Channel;
    console.log('✅ Connected to RabbitMQ');
  }

  async sendMessage(queue: string, message: Record<string, any>) {
    if (!this.channel) throw new Error('RabbitMQ channel not initialized');
    (await this.channel.assertQueue(queue, {
      durable: true,
    })) as amqp.Replies.AssertQueue;
    this.channel.sendToQueue(queue, Buffer.from(JSON.stringify(message)));
    console.log(`📨 Message sent to queue "${queue}"`, message);
  }
}
