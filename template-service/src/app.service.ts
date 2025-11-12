import { Injectable } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';

@Injectable()
export class AppService {
  constructor(
    @InjectDataSource()
    private dataSource: DataSource,
  ) {}

  getHello(): string {
    return 'Template Service API';
  }

  async getHealth() {
    try {
      await this.dataSource.query('SELECT 1');
      return {
        success: true,
        message: 'Template Service is healthy',
        data: {
          status: 'healthy',
          service: 'template-service',
          version: '1.0.0',
          checks: {
            database: 'ok',
          },
        },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Template Service is unhealthy',
        data: {
          status: 'unhealthy',
          service: 'template-service',
          version: '1.0.0',
          checks: {
            database: 'error',
          },
        },
      };
    }
  }
}
