import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './user/user.entity';

@Injectable()
export class AppService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
  ) {}

  getHello(): string {
    return 'User Service is running';
  }

  async getHealth() {
    try {
      // Test database connection
      await this.userRepository.query('SELECT 1');

      return {
        success: true,
        message: 'User Service is healthy',
        data: {
          status: 'healthy',
          service: 'user-service-nestjs',
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
          service: 'user-service-nestjs',
          version: '1.0.0',
          checks: {
            database: 'failed',
          },
        },
      };
    }
  }
}
