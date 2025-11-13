import { Controller, Get, Post, Put, Body, Param, ParseUUIDPipe, UseInterceptors } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam, ApiBody } from '@nestjs/swagger';
import { UserService } from './user.service';
import { User } from './user.entity';
import { 
  CreateUserDto, 
  UpdateUserDto, 
  UserResponseDto, 
  ApiResponseDto,
  UpdatePreferencesDto,
  UpdatePushTokenDto
} from './dto';
import { ResponseInterceptor } from '../common/interceptors/response.interceptor';

@ApiTags('users')
@Controller('users')
@UseInterceptors(ResponseInterceptor)
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @ApiOperation({ summary: 'Get all users' })
  @ApiResponse({ 
    status: 200, 
    description: 'Return all users',
    type: ApiResponseDto<UserResponseDto[]>
  })
  findAll(): Promise<User[]> {
    return this.userService.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'User UUID' })
  @ApiResponse({ 
    status: 200, 
    description: 'Return user',
    type: ApiResponseDto<UserResponseDto>
  })
  findOne(@Param('id', ParseUUIDPipe) id: string): Promise<User> {
    return this.userService.findOne(id);
  }

  @Post()
  @ApiOperation({ summary: 'Create new user' })
  @ApiBody({ type: CreateUserDto })
  @ApiResponse({ 
    status: 201, 
    description: 'User created successfully',
    type: ApiResponseDto<UserResponseDto>
  })
  create(@Body() userData: CreateUserDto): Promise<User> {
    return this.userService.create(userData);
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update user' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'User UUID' })
  @ApiBody({ type: UpdateUserDto })
  @ApiResponse({ 
    status: 200, 
    description: 'User updated successfully',
    type: ApiResponseDto<UserResponseDto>
  })
  update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() userData: UpdateUserDto,
  ): Promise<User> {
    return this.userService.update(id, userData);
  }

  @Get(':id/preferences')
  @ApiOperation({ summary: 'Get user preferences' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'User UUID' })
  @ApiResponse({ 
    status: 200, 
    description: 'Return user preferences',
    schema: {
      type: 'object',
      properties: {
        success: { type: 'boolean', example: true },
        message: { type: 'string', example: 'User preferences retrieved successfully' },
        data: {
          type: 'object',
          properties: {
            user_id: { type: 'string', format: 'uuid' },
            preferences: {
              type: 'object',
              properties: {
                email: { type: 'boolean' },
                push: { type: 'boolean' }
              }
            }
          }
        },
        error: { type: 'null' },
        meta: { type: 'null' }
      }
    }
  })
  getPreferences(@Param('id', ParseUUIDPipe) id: string) {
    return this.userService.getPreferences(id);
  }

  @Put(':id/preferences')
  @ApiOperation({ summary: 'Update user preferences' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'User UUID' })
  @ApiBody({ type: UpdatePreferencesDto })
  @ApiResponse({ 
    status: 200, 
    description: 'Preferences updated successfully',
    schema: {
      type: 'object',
      properties: {
        success: { type: 'boolean', example: true },
        message: { type: 'string', example: 'User preferences updated successfully' },
        data: {
          type: 'object',
          properties: {
            user_id: { type: 'string', format: 'uuid' },
            preferences: {
              type: 'object',
              properties: {
                email: { type: 'boolean' },
                push: { type: 'boolean' }
              }
            }
          }
        },
        error: { type: 'null' },
        meta: { type: 'null' }
      }
    }
  })
  updatePreferences(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() preferences: UpdatePreferencesDto,
  ) {
    return this.userService.updatePreferences(id, preferences);
  }

  @Put(':id/push-token')
  @ApiOperation({ summary: 'Update user push token' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'User UUID' })
  @ApiBody({ type: UpdatePushTokenDto })
  @ApiResponse({ 
    status: 200, 
    description: 'Push token updated successfully',
    schema: {
      type: 'object',
      properties: {
        success: { type: 'boolean', example: true },
        message: { type: 'string', example: 'Push token updated successfully' },
        data: {
          type: 'object',
          properties: {
            user_id: { type: 'string', format: 'uuid' }
          }
        },
        error: { type: 'null' },
        meta: { type: 'null' }
      }
    }
  })
  updatePushToken(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: UpdatePushTokenDto,
  ) {
    return this.userService.updatePushToken(id, body.push_token);
  }
}
