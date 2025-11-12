import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class AppService {
  private prisma = new PrismaClient();

  getHello(): string {
    return 'Template Service is running';
  }

  async getHealth() {
    try {
      // Test database connection
      await this.prisma.$queryRaw`SELECT 1`;
      
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
        message: 'Service unhealthy',
        error: error.message,
        data: {
          status: 'unhealthy',
          service: 'template-service',
          version: '1.0.0',
          checks: {
            database: 'failed',
          },
        },
      };
    }
  }

  async onModuleDestroy() {
    await this.prisma.$disconnect();
  }
}
