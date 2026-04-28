from predict import load_model ,generate_caption
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from rclpy.node import Node
from pathlib import Path
import rclpy

class FastVLMNode(Node):
    def __init__(self):
        super().__init__('fastvlm_caption_node')
        self.get_logger().info('FastVLM Caption Node Starting...')

        # Declare parameters
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('caption_topic', '/visual_memory/caption')
        self.declare_parameter('caption_interval', 3.0)
        self.declare_parameter('model_path', '~/Desktop/checkpoints/llava-fastvithd_1.5b_stage3')

        # Get parameters
        self.image_topic = self.get_parameter('image_topic').value
        self.caption_topic = self.get_parameter('caption_topic').value
        self.caption_interval = self.get_parameter('caption_interval').value
        model_path_str = self.get_parameter('model_path').value
        self.model_path = Path(model_path_str).expanduser()
        
        # Setup
        self.bridge = CvBridge()
        self.current_image = None
        
        load_model(self.model_path)

        # Publishers & Subscribers
        self.caption_pub = self.create_publisher(String, self.caption_topic, 10)
        self.image_sub = self.create_subscription(Image, self.image_topic, self.image_callback, 10)

        # Timer for periodic captioning (handles rate limiting)
        self.timer = self.create_timer(self.caption_interval, self.caption_timer_callback)
        
    def image_callback(self, msg):
        """Store latest image from Gazebo/camera"""
        try:
            self.current_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception as e:
            self.get_logger().warn(f'Image conversion failed: {e}')
    
    def caption_timer_callback(self):
        """Generate caption every X seconds if new image available"""
        if self.current_image is None: return 

        caption = self.generate_caption(self.current_image)
        if caption:
            msg = String()
            msg.data = caption
            self.caption_pub.publish(msg)
            self.get_logger().info(f'caption generated: {caption}')
    
    def generate_caption(self, cv_image):
        """Generate caption using FastVLM"""
        try:
            return generate_caption(cv_image=cv_image)
            
        except Exception as e:
            self.get_logger().error(f'Caption generation failed: {e}')
            return None

def main(args=None):
    rclpy.init(args=args)
    node = FastVLMNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()