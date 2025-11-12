import { Controller, Get, Post, Put, Body, Param } from '@nestjs/common';
import { UserService } from './user.service';
import { User } from './user.entity';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  findAll(): Promise<User[]> {
    return this.userService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string): Promise<User> {
    return this.userService.findOne(+id);
  }

  @Post()
  create(@Body() userData: Partial<User>): Promise<User> {
    return this.userService.create(userData);
  }

  @Put(':id')
  update(@Param('id') id: string, @Body() userData: Partial<User>): Promise<User> {
    return this.userService.update(+id, userData);
  }

  @Get(':id/preferences')
  getPreferences(@Param('id') id: string) {
    return this.userService.getPreferences(+id);
  }

  @Put(':id/preferences')
  updatePreferences(
    @Param('id') id: string,
    @Body() preferences: { email?: boolean; push?: boolean },
  ) {
    return this.userService.updatePreferences(+id, preferences);
  }

  @Put(':id/push-token')
  updatePushToken(
    @Param('id') id: string,
    @Body() body: { push_token: string },
  ) {
    return this.userService.updatePushToken(+id, body.push_token);
  }
}
