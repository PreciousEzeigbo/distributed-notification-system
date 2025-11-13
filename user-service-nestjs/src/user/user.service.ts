import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './user.entity';
import { RabbitMQService } from '../rabbitmq.service';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,

    private readonly rabbitMQService: RabbitMQService,
  ) {}

  findAll() {
    return this.userRepository.find();
  }

  async findOne(id: string): Promise<User> {
    const user = await this.userRepository.findOne({ where: { id } });
    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`);
    }
    return user;
  }

  async create(userData: Partial<User>) {
    // Set default preferences if not provided
    if (!userData.preferences) {
      userData.preferences = { email: true, push: true };
    }

    // Save the user
    const user = this.userRepository.create(userData);
    const savedUser = await this.userRepository.save(user);

    // Notify RabbitMQ that a new user has been created
    await this.rabbitMQService.sendMessage('user_created', {
      id: savedUser.id,
      email: savedUser.email,
      preferences: savedUser.preferences,
    });

    console.log('📢 User creation event sent to RabbitMQ:', savedUser);

    return savedUser;
  }

  async update(id: string, userData: Partial<User>): Promise<User> {
    const user = await this.findOne(id);
    Object.assign(user, userData);
    return this.userRepository.save(user);
  }

  async getPreferences(id: string) {
    const user = await this.findOne(id);
    return {
      success: true,
      message: 'User preferences retrieved successfully',
      data: {
        user_id: user.id,
        preferences: user.preferences,
      },
    };
  }

  async updatePreferences(
    id: string,
    preferences: { email?: boolean; push?: boolean },
  ) {
    const user = await this.findOne(id);
    user.preferences = { ...user.preferences, ...preferences };
    await this.userRepository.save(user);

    // Notify about preference change
    await this.rabbitMQService.sendMessage('user_preferences_updated', {
      user_id: id,
      preferences: user.preferences,
    });

    return {
      success: true,
      message: 'User preferences updated successfully',
      data: {
        user_id: user.id,
        preferences: user.preferences,
      },
    };
  }

  async updatePushToken(id: string, push_token: string) {
    const user = await this.findOne(id);
    user.push_token = push_token;
    await this.userRepository.save(user);

    return {
      success: true,
      message: 'Push token updated successfully',
      data: {
        user_id: user.id,
        push_token: user.push_token,
      },
    };
  }
}
