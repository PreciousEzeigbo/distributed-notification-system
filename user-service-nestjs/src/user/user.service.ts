import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './user.entity';
import { RabbitMQService } from '../rabbitmq.service';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,

    private readonly rabbitMQService: RabbitMQService, // 👈 add this
  ) {}

  findAll() {
    return this.userRepository.find();
  }

  async create(userData: Partial<User>) {
    // 1️⃣ Save the user
    const user = this.userRepository.create(userData);
    const savedUser = await this.userRepository.save(user);

    // 2️⃣ Notify RabbitMQ that a new user has been created
    await this.rabbitMQService.sendMessage('user_created', {
      id: savedUser.id,
      email: savedUser.email,
      name: savedUser.name,
    });

    console.log('📢 User creation event sent to RabbitMQ:', savedUser);

    // 3️⃣ Return the created user
    return savedUser;
  }
}
