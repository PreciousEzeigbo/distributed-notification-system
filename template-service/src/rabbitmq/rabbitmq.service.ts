import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import * as amqp from 'amqplib';

@Injectable()
export class RabbitMQService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RabbitMQService.name);
  private connection: amqp.Connection;
  private channel: amqp.Channel;
  private readonly url = process.env.RABBITMQ_URL || 'amqp://admin:admin@rabbitmq:5672';

  async onModuleInit() {
    await this.connect();
  }

  async connect() {
    try {
      this.connection = await amqp.connect(this.url, { heartbeat: 60 });
      this.channel = await this.connection.createChannel();
      await this.channel.assertExchange('notifications.direct', 'direct', { durable: true });

      this.connection.on('error', (err) => this.logger.error('Connection error', err));
      this.connection.on('close', () => this.reconnect());

      this.logger.log('Connected to RabbitMQ');
    } catch (err) {
      this.logger.error('Failed to connect to RabbitMQ', err);
      setTimeout(() => this.connect(), 5000);
    }
  }

  private async reconnect() {
    this.logger.warn('RabbitMQ disconnected. Reconnecting...');
    setTimeout(() => this.connect(), 5000);
  }

  async publish(routingKey: string, message: any) {
    if (!this.channel) {
      this.logger.warn('Channel not ready, retrying publish...');
      setTimeout(() => this.publish(routingKey, message), 1000);
      return;
    }
    this.channel.publish(
      'notifications.direct',
      routingKey,
      Buffer.from(JSON.stringify(message)),
      { persistent: true }
    );
  }

  async consume(queue: string, callback: (msg: any) => Promise<void>) {
    await this.channel.assertQueue(queue, { durable: true });
    this.channel.consume(queue, async (msg) => {
      if (msg) {
        try {
          const data = JSON.parse(msg.content.toString());
          await callback(data);
          this.channel.ack(msg);
        } catch (err) {
          this.logger.error('Error processing message', err);
          this.channel.nack(msg, false, false);
        }
      }
    });
  }

  async onModuleDestroy() {
    await this.channel?.close();
    await this.connection?.close();
  }
}